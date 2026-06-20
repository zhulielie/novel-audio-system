from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
import os
import shutil
import base64
import tempfile
import json as json_mod
import time as time_mod

from .models import TTSEngine, VoiceAsset, TTSGenerationTask, TTSSegmentResult
from .serializers import (
    TTSEngineSerializer, TTSEngineListSerializer,
    VoiceAssetSerializer, VoiceAssetListSerializer,
    TTSGenerationTaskSerializer, TTSGenerationTaskListSerializer,
    TTSSegmentResultSerializer, TTSGenerationRequestSerializer
)
from .services import get_tts_service, run_tts_generation_task

# VoxCPM 模型全局缓存
_voxcpm_model = None


def _get_voxcpm_model():
    """懒加载 VoxCPM 模型，全局复用"""
    global _voxcpm_model
    if _voxcpm_model is None:
        import sys
        tts_bench_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark')
        if tts_bench_dir not in sys.path:
            sys.path.insert(0, tts_bench_dir)
        from voxcpm import VoxCPM
        model_dir = os.path.join(tts_bench_dir, 'models', 'voxcpm2')
        _voxcpm_model = VoxCPM.from_pretrained(model_dir, load_denoiser=False, device="cuda:0")
    return _voxcpm_model


class TTSEngineViewSet(viewsets.ModelViewSet):
    """TTS 引擎视图集"""
    queryset = TTSEngine.objects.all().order_by('-is_default', '-priority', 'name')
    serializer_class = TTSEngineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['engine_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'created_at', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return TTSEngineListSerializer
        return TTSEngineSerializer

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试引擎连接"""
        engine = self.get_object()
        try:
            if engine.engine_type == 'edge_tts':
                return Response({'success': True, 'message': 'Edge TTS 无需连接测试'})
            elif engine.api_url:
                import requests
                response = requests.get(engine.api_url, timeout=5)
                return Response({
                    'success': response.status_code < 500,
                    'status_code': response.status_code,
                    'message': '连接测试完成'
                })
            else:
                return Response({'success': True, 'message': '本地引擎，无需连接测试'})
        except Exception as e:
            return Response({
                'success': False,
                'message': f'连接失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设为默认引擎"""
        engine = self.get_object()
        TTSEngine.objects.all().update(is_default=False)
        engine.is_default = True
        engine.save()
        return Response({
            'success': True,
            'message': f'{engine.name} 已设为默认引擎'
        })

    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取所有引擎类型"""
        return Response([
            {'value': v[0], 'label': v[1]}
            for v in TTSEngine.ENGINE_CHOICES
        ])

    @action(detail=False, methods=['post'])
    def init_defaults(self, request):
        """初始化默认引擎配置"""
        defaults = [
            {
                'name': 'GPT-SoVITS (本地)',
                'engine_type': 'gpt_sovits',
                'api_url': 'http://127.0.0.1:9880',
                'is_local': True,
                'default_params': {'text_language': 'zh', 'prompt_language': 'zh'},
                'is_default': True,
                'priority': 10,
            },
            {
                'name': 'Edge TTS (在线)',
                'engine_type': 'edge_tts',
                'api_url': '',
                'is_local': False,
                'default_params': {'voice': 'zh-CN-XiaoxiaoNeural', 'rate': '+0%'},
                'is_default': False,
                'priority': 5,
            },
            {
                'name': 'XTTS API',
                'engine_type': 'xtts',
                'api_url': 'http://127.0.0.1:8020/tts',
                'is_local': True,
                'default_params': {'language': 'zh'},
                'is_default': False,
                'priority': 8,
            },
            {
                'name': 'IndexTTS (本地GPU)',
                'engine_type': 'indextts',
                'api_url': '',
                'is_local': True,
                'default_params': {},
                'is_default': False,
                'priority': 9,
            },
        ]

        created = []
        for config in defaults:
            engine, was_created = TTSEngine.objects.get_or_create(
                engine_type=config['engine_type'],
                defaults=config
            )
            if was_created:
                created.append(engine.name)

        return Response({
            'success': True,
            'created': created,
            'message': f'已创建 {len(created)} 个默认引擎配置'
        })


class VoiceAssetViewSet(viewsets.ModelViewSet):
    """语音资源视图集"""
    queryset = VoiceAsset.objects.all().order_by('-is_active', 'voice_type', 'name')
    serializer_class = VoiceAssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voice_type', 'is_active', 'character']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'name', 'voice_type']

    def get_serializer_class(self):
        if self.action == 'list':
            return VoiceAssetListSerializer
        return VoiceAssetSerializer

    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取声音类型列表"""
        return Response([
            {'value': v[0], 'label': v[1]}
            for v in VoiceAsset.VOICE_TYPE_CHOICES
        ])

    @action(detail=False, methods=['post'])
    def import_from_media(self, request):
        """从 media/voices 目录导入语音资源"""
        voices_dir = os.path.join(os.path.dirname(__file__), '..', 'media', 'voices')
        voices_dir = os.path.abspath(voices_dir)

        if not os.path.exists(voices_dir):
            return Response({
                'success': False,
                'message': f'目录不存在: {voices_dir}'
            }, status=status.HTTP_404_NOT_FOUND)

        imported = []
        for filename in os.listdir(voices_dir):
            if not filename.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a')):
                continue

            filepath = os.path.join(voices_dir, filename)
            name = os.path.splitext(filename)[0]

            # 判断声音类型
            voice_type = 'custom'
            if '旁白' in name or 'narrator' in name.lower():
                voice_type = 'narrator'
            elif '男' in name or 'male' in name.lower():
                voice_type = 'male'
            elif '女' in name or 'female' in name.lower():
                voice_type = 'female'

            # 复制到上传目录
            from django.core.files import File
            with open(filepath, 'rb') as f:
                asset, created = VoiceAsset.objects.get_or_create(
                    name=name,
                    defaults={
                        'voice_type': voice_type,
                        'description': f'从 {filename} 导入',
                    }
                )
                if created:
                    asset.audio_file.save(filename, File(f), save=True)
                    imported.append(name)

        return Response({
            'success': True,
            'imported': imported,
            'message': f'成功导入 {len(imported)} 个语音资源'
        })

    @action(detail=False, methods=['post'])
    def quick_assign_character(self, request):
        """快速关联角色到语音资源"""
        voice_id = request.data.get('voice_id')
        character_id = request.data.get('character_id')

        if not voice_id or not character_id:
            return Response({
                'success': False,
                'message': '需要提供 voice_id 和 character_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            asset = VoiceAsset.objects.get(id=voice_id)
            from novels.models import Character
            character = Character.objects.get(id=character_id)
            asset.character = character
            asset.save()
            return Response({
                'success': True,
                'message': f'已将 {asset.name} 关联到角色 {character.name}'
            })
        except VoiceAsset.DoesNotExist:
            return Response({'success': False, 'message': '语音资源不存在'}, status=404)
        except Character.DoesNotExist:
            return Response({'success': False, 'message': '角色不存在'}, status=404)


class TTSGenerationTaskViewSet(viewsets.ModelViewSet):
    """TTS 生成任务视图集"""
    queryset = TTSGenerationTask.objects.all().order_by('-created_at')
    serializer_class = TTSGenerationTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'novel', 'chapter', 'engine']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'started_at', 'completed_at', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return TTSGenerationTaskListSerializer
        return TTSGenerationTaskSerializer

    @action(detail=False, methods=['post'])
    def create_and_start(self, request):
        """创建并启动 TTS 生成任务"""
        serializer = TTSGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            from novels.models import Novel, Chapter
            novel = Novel.objects.get(id=data['novel_id'])
            chapter = None
            if data.get('chapter_id'):
                chapter = Chapter.objects.get(id=data['chapter_id'])
        except Novel.DoesNotExist:
            return Response({'success': False, 'message': '小说不存在'}, status=404)
        except Chapter.DoesNotExist:
            return Response({'success': False, 'message': '章节不存在'}, status=404)

        # 获取引擎
        engine = None
        if data.get('engine_id'):
            try:
                engine = TTSEngine.objects.get(id=data['engine_id'])
            except TTSEngine.DoesNotExist:
                pass

        if not engine:
            engine = TTSEngine.objects.filter(is_active=True).order_by('-is_default', '-priority').first()

        if not engine:
            return Response({
                'success': False,
                'message': '没有可用的 TTS 引擎，请先配置引擎'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建任务
        task = TTSGenerationTask.objects.create(
            name=data['name'],
            novel=novel,
            chapter=chapter,
            engine=engine,
            script_data=data.get('script_data', []),
            speaker_voice_map=data.get('speaker_voice_map', {}),
            generation_params=data.get('generation_params', {}),
            status='pending'
        )

        # 启动后台任务
        try:
            from django_q.tasks import async_task
            async_task(run_tts_generation_task, task.id)
            task.status = 'preparing'
            task.save()
        except ImportError:
            # 如果没有 django-q，同步执行
            import threading
            thread = threading.Thread(target=run_tts_generation_task, args=(task.id,))
            thread.start()

        return Response({
            'success': True,
            'task_id': task.id,
            'message': 'TTS 生成任务已创建并启动',
            'task': TTSGenerationTaskListSerializer(task).data
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """获取任务进度"""
        task = self.get_object()
        segments = task.segment_results.all().order_by('sequence_number')
        segment_serializer = TTSSegmentResultSerializer(segments, many=True)

        return Response({
            'task': TTSGenerationTaskListSerializer(task).data,
            'segments': segment_serializer.data,
        })

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载合并后的音频"""
        task = self.get_object()
        if task.merged_audio_path and os.path.exists(task.merged_audio_path):
            from django.http import FileResponse
            return FileResponse(
                open(task.merged_audio_path, 'rb'),
                as_attachment=True,
                filename=f'{task.name}_合成音频.wav'
            )
        return Response({'success': False, 'message': '音频文件不存在'}, status=404)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消任务"""
        task = self.get_object()
        if task.status in ['pending', 'preparing', 'generating']:
            task.status = 'cancelled'
            task.save()
            return Response({'success': True, 'message': '任务已取消'})
        return Response({
            'success': False,
            'message': f'当前状态 {task.get_status_display()} 无法取消'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的任务"""
        task = self.get_object()
        if task.status == 'failed':
            task.status = 'pending'
            task.error_message = ''
            task.completed_segments = 0
            task.failed_segments = 0
            task.progress = 0
            task.save()

            try:
                from django_q.tasks import async_task
                async_task(run_tts_generation_task, task.id)
            except ImportError:
                import threading
                thread = threading.Thread(target=run_tts_generation_task, args=(task.id,))
                thread.start()

            return Response({
                'success': True,
                'message': '任务已重置并重新启动',
                'task': TTSGenerationTaskListSerializer(task).data
            })
        return Response({
            'success': False,
            'message': '只有失败的任务可以重试'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def quick_synthesize(self, request):
        """快速合成 - 从章节内容自动生成剧本并合成"""
        novel_id = request.data.get('novel_id')
        chapter_id = request.data.get('chapter_id')
        speaker_configs = request.data.get('speaker_configs', {})

        if not novel_id or not chapter_id:
            return Response({
                'success': False,
                'message': '需要提供 novel_id 和 chapter_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from novels.models import Novel, Chapter
            novel = Novel.objects.get(id=novel_id)
            chapter = Chapter.objects.get(id=chapter_id, novel=novel)
        except (Novel.DoesNotExist, Chapter.DoesNotExist):
            return Response({'success': False, 'message': '小说或章节不存在'}, status=404)

        # 简单解析章节内容为剧本
        content = chapter.content or ''
        # 这里简化处理：按段落分割，第一段旁白，后面根据引号判断
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]

        script_data = []
        for i, para in enumerate(paragraphs[:50]):  # 最多50段
            # 简单规则：包含引号的为对话，否则为旁白
            if '"' in para or '"' in para or '"' in para:
                # 提取引号内内容和说话人（简化处理）
                script_data.append({
                    'speaker': speaker_configs.get('dialogue', '韩立'),
                    'text': para,
                    'emotion': ''
                })
            else:
                script_data.append({
                    'speaker': speaker_configs.get('narrator', '旁白'),
                    'text': para,
                    'emotion': ''
                })

        # 获取默认语音映射
        speaker_voice_map = {}
        default_edge_voices = {
            '旁白': 'zh-CN-YunyangNeural',
            '韩立': 'zh-CN-XiaoxiaoNeural',
        }

        engine = TTSEngine.objects.filter(is_active=True).order_by('-is_default', '-priority').first()

        for speaker_name in set(s['speaker'] for s in script_data):
            # 查找匹配的语音资源
            asset = VoiceAsset.objects.filter(
                Q(name__icontains=speaker_name) | Q(character__name__icontains=speaker_name),
                is_active=True
            ).first()

            # EdgeTTS 无需参考音频，自动创建映射
            if not asset and engine and engine.engine_type == 'edge_tts':
                edge_voice = default_edge_voices.get(speaker_name, 'zh-CN-XiaoxiaoNeural')
                asset, _ = VoiceAsset.objects.get_or_create(
                    name=f'{speaker_name} ({edge_voice})',
                    defaults={
                        'voice_type': 'narrator' if '旁白' in speaker_name else 'male',
                        'description': f'EdgeTTS 自动映射音色: {edge_voice}',
                        'tags': f'edge_tts,{edge_voice}',
                    }
                )

            if asset:
                speaker_voice_map[speaker_name] = asset.id

        if not speaker_voice_map:
            return Response({
                'success': False,
                'message': '未找到可用的语音资源，请先导入语音资源或配置 EdgeTTS 引擎'
            }, status=status.HTTP_400_BAD_REQUEST)
        task = TTSGenerationTask.objects.create(
            name=f'{novel.title} - {chapter.title} 快速合成',
            novel=novel,
            chapter=chapter,
            engine=engine,
            script_data=script_data,
            speaker_voice_map=speaker_voice_map,
            status='pending'
        )

        try:
            from django_q.tasks import async_task
            async_task(run_tts_generation_task, task.id)
        except ImportError:
            import threading
            thread = threading.Thread(target=run_tts_generation_task, args=(task.id,))
            thread.start()

        return Response({
            'success': True,
            'task_id': task.id,
            'message': f'已创建快速合成任务，共 {len(script_data)} 段',
            'script_preview': script_data[:5],
            'speaker_voice_map': speaker_voice_map,
            'task': TTSGenerationTaskListSerializer(task).data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取 TTS 任务统计"""
        total = self.queryset.count()
        completed = self.queryset.filter(status='completed').count()
        failed = self.queryset.filter(status='failed').count()
        running = self.queryset.filter(status__in=['preparing', 'generating', 'merging']).count()

        total_duration = sum(
            t.total_duration or 0 for t in self.queryset.filter(status='completed')
        )

        return Response({
            'total_tasks': total,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'running_tasks': running,
            'total_duration': round(total_duration, 2),
            'success_rate': round(completed / total * 100, 2) if total > 0 else 0
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def voxcpm_synthesize(request):
    """VoxCPM 2.0 语音合成 API（调参 playground）
    
    请求体 JSON:
        text: str                - 合成文本
        cfg_value: float = 2.0   - 引导强度 (1.0~3.0)
        inference_timesteps: int = 10 - 推理步数 (5~20)
        mode: str = "base"       - "base"音色设计 / "clone"声音克隆
        reference_audio: str = "" - 克隆模式下的参考音频路径
    """
    try:
        text = request.data.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'message': '请输入文本'}, status=400)
        if len(text) > 500:
            return JsonResponse({'success': False, 'message': '文本过长，最多500字'}, status=400)

        cfg_value = float(request.data.get('cfg_value', 2.0))
        cfg_value = max(1.0, min(3.0, cfg_value))

        inference_timesteps = int(request.data.get('inference_timesteps', 10))
        inference_timesteps = max(5, min(20, inference_timesteps))

        mode = request.data.get('mode', 'base')
        reference_audio = request.data.get('reference_audio', '')
        normalize = request.data.get('normalize', False)
        denoise = request.data.get('denoise', False)
        max_len = int(request.data.get('max_len', 4096))

        import time
        model = _get_voxcpm_model()

        kwargs = {
            'text': text,
            'cfg_value': cfg_value,
            'inference_timesteps': inference_timesteps,
            'normalize': normalize,
            'denoise': denoise,
            'max_len': max_len,
        }

        if mode == 'clone' and reference_audio and os.path.exists(reference_audio):
            kwargs['reference_wav_path'] = reference_audio

        t0 = time.time()
        wav = model.generate(**kwargs)
        elapsed = time.time() - t0
        duration = len(wav) / model.tts_model.sample_rate

        # 保存 WAV + 参数到 outputs 目录
        import io, json as json_mod
        import soundfile as sf
        tts_output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark', 'outputs')
        os.makedirs(tts_output_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        name = f'voxcpm_{mode}_{timestamp}.wav'
        fpath = os.path.join(tts_output_dir, name)
        sf.write(fpath, wav, model.tts_model.sample_rate)
        
        # 保存参数
        params = {
            'text': text,
            'mode': mode,
            'cfg_value': cfg_value,
            'inference_timesteps': inference_timesteps,
            'normalize': normalize,
            'denoise': denoise,
            'max_len': max_len,
            'reference_audio': reference_audio if mode == 'clone' else '',
            'duration': round(duration, 2),
            'runtime': round(elapsed, 2),
            'rtf': round(elapsed / duration, 2) if duration > 0 else 0,
            'sample_rate': int(model.tts_model.sample_rate),
            'timestamp': timestamp,
        }
        json_path = fpath.replace('.wav', '.json')
        with open(json_path, 'w', encoding='utf-8') as jf:
            json_mod.dump(params, jf, ensure_ascii=False, indent=2)

        # 转 base64 返回
        buf = io.BytesIO()
        sf.write(buf, wav, model.tts_model.sample_rate, format='WAV')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()

        return JsonResponse({
            'success': True,
            'audio_base64': b64,
            'duration': round(duration, 2),
            'sample_rate': model.tts_model.sample_rate,
            'runtime': round(elapsed, 2),
            'rtf': round(elapsed / duration, 2) if duration > 0 else 0,
            'filename': name,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def voxcpm_outputs(request):
    """列出已生成的 VoxCPM 音频文件及参数"""
    tts_bench_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark', 'outputs')
    files = []
    if os.path.exists(tts_bench_dir):
        for f in sorted(os.listdir(tts_bench_dir), key=lambda x: os.path.getmtime(os.path.join(tts_bench_dir, x)), reverse=True):
            # 只显示 voxcpm_ 开头的
            if not f.lower().startswith('voxcpm_') or not f.lower().endswith('.wav'):
                continue
            fpath = os.path.join(tts_bench_dir, f)
            size_kb = round(os.path.getsize(fpath) / 1024, 1)
            # 读取参数 JSON
            params = {}
            json_path = fpath.replace('.wav', '.json')
            try:
                import json as json_mod
                with open(json_path, 'r', encoding='utf-8') as jf:
                    params = json_mod.load(jf)
                dur = params.get('duration', 0)
            except:
                try:
                    import soundfile as sf
                    info = sf.info(fpath)
                    dur = round(info.duration, 1)
                except:
                    dur = 0
            files.append({
                'name': f,
                'size_kb': size_kb,
                'duration': dur,
                'url': f'/api/tts/voxcpm/outputs/{f}/',
                'params': params,
            })
    return JsonResponse({'success': True, 'files': files})


@api_view(['GET'])
@permission_classes([AllowAny])
def voxcpm_output_file(request, filename):
    """提供音频文件下载"""
    tts_bench_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark', 'outputs')
    fpath = os.path.join(tts_bench_dir, filename)
    if not os.path.exists(fpath) or '..' in filename:
        return JsonResponse({'success': False, 'message': '文件不存在'}, status=404)
    from django.http import FileResponse
    return FileResponse(open(fpath, 'rb'), content_type='audio/wav')


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def voxcpm_references(request):
    """管理保存的参考音频"""
    tts_bench_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark', 'outputs')
    refs_file = os.path.join(tts_bench_dir, 'voxcpm_references.json')
    os.makedirs(tts_bench_dir, exist_ok=True)

    if request.method == 'POST':
        filename = request.data.get('filename', '')
        label = request.data.get('label', '')
        if not filename:
            return JsonResponse({'success': False, 'message': '缺少 filename'}, status=400)
        fpath = os.path.join(tts_bench_dir, filename)
        if not os.path.exists(fpath):
            return JsonResponse({'success': False, 'message': '文件不存在'}, status=404)

        # 读取现有参考列表
        refs = []
        if os.path.exists(refs_file):
            with open(refs_file, 'r', encoding='utf-8') as f:
                refs = json_mod.load(f)

        # 去重
        refs = [r for r in refs if r['filename'] != filename]
        item = {'filename': filename, 'label': label or filename, 'added_at': time_mod.strftime('%Y-%m-%d %H:%M:%S')}
        refs.insert(0, item)
        with open(refs_file, 'w', encoding='utf-8') as f:
            json_mod.dump(refs, f, ensure_ascii=False, indent=2)
        return JsonResponse({'success': True, 'references': refs})

    # GET
    refs = []
    if os.path.exists(refs_file):
        with open(refs_file, 'r', encoding='utf-8') as f:
            refs = json_mod.load(f)
    # 追加完整路径和参数
    for r in refs:
        fpath = os.path.join(tts_bench_dir, r['filename'])
        r['path'] = fpath
        r['exists'] = os.path.exists(fpath)
        json_path = fpath.replace('.wav', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as jf:
                r['params'] = json_mod.load(jf)
    return JsonResponse({'success': True, 'references': refs})


@api_view(['DELETE'])
@permission_classes([AllowAny])
def voxcpm_reference_delete(request, filename):
    """删除一个参考"""
    tts_bench_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tts_benchmark', 'outputs')
    refs_file = os.path.join(tts_bench_dir, 'voxcpm_references.json')
    if os.path.exists(refs_file):
        with open(refs_file, 'r', encoding='utf-8') as f:
            refs = json_mod.load(f)
        refs = [r for r in refs if r['filename'] != filename]
        with open(refs_file, 'w', encoding='utf-8') as f:
            json_mod.dump(refs, f, ensure_ascii=False, indent=2)
    return JsonResponse({'success': True})
