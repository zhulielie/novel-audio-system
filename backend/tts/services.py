"""
TTS 合成服务
封装多说话人音频合成逻辑，支持多种 TTS 引擎
"""
import os
import json
import time
import shutil
import traceback
from pathlib import Path
from django.conf import settings


class BaseTTSService:
    """TTS 服务基类"""

    def __init__(self, engine_config):
        self.engine = engine_config
        self.api_url = engine_config.api_url if engine_config else ''

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        """合成单段音频，子类必须实现"""
        raise NotImplementedError

    def synthesize_batch(self, segments, speaker_voice_map, output_dir, progress_callback=None):
        """批量合成音频"""
        results = []
        total = len(segments)

        for i, segment in enumerate(segments):
            speaker = segment.get('speaker', '旁白')
            text = segment.get('text', '')
            emotion = segment.get('emotion', '')

            voice_asset_id = speaker_voice_map.get(speaker)
            if not voice_asset_id:
                results.append({
                    'index': i,
                    'status': 'failed',
                    'error': f'角色 {speaker} 没有配置语音资源'
                })
                if progress_callback:
                    progress_callback(i + 1, total)
                continue

            try:
                from .models import VoiceAsset
                voice_asset = VoiceAsset.objects.get(id=voice_asset_id)
            except VoiceAsset.DoesNotExist:
                results.append({
                    'index': i,
                    'status': 'failed',
                    'error': f'语音资源 {voice_asset_id} 不存在'
                })
                if progress_callback:
                    progress_callback(i + 1, total)
                continue

            output_path = os.path.join(output_dir, f'segment_{i+1:04d}_{speaker}.wav')

            try:
                self.synthesize(text, voice_asset, output_path, emotion=emotion)
                results.append({
                    'index': i,
                    'status': 'completed',
                    'output_path': output_path,
                    'speaker': speaker
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'status': 'failed',
                    'error': str(e)
                })

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def merge_audio(self, audio_paths, output_path, pause_duration=0.5):
        """合并音频片段"""
        try:
            import torch
            import torchaudio

            merged = []
            sample_rate = None

            for i, path in enumerate(audio_paths):
                if not os.path.exists(path):
                    continue
                audio, sr = torchaudio.load(path)
                if sample_rate is None:
                    sample_rate = sr
                elif sr != sample_rate:
                    audio = torchaudio.transforms.Resample(sr, sample_rate)(audio)

                merged.append(audio)

                # 添加停顿
                if i < len(audio_paths) - 1:
                    pause_samples = int(pause_duration * sample_rate)
                    pause = torch.zeros(audio.shape[0], pause_samples)
                    merged.append(pause)

            if merged:
                final = torch.cat(merged, dim=-1)
                torchaudio.save(output_path, final, sample_rate)
                return output_path
            return None
        except ImportError:
            # 如果没有 torchaudio，使用 ffmpeg
            return self._merge_with_ffmpeg(audio_paths, output_path, pause_duration)
        except Exception as e:
            print(f'合并音频失败: {e}')
            traceback.print_exc()
            return None

    def _merge_with_ffmpeg(self, audio_paths, output_path, pause_duration=0.5):
        """使用 ffmpeg 合并音频"""
        import subprocess
        import tempfile

        # 创建文件列表
        list_file = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
        with open(list_file, 'w', encoding='utf-8') as f:
            for path in audio_paths:
                if os.path.exists(path):
                    f.write(f"file '{path}'\n")

        try:
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-acodec', 'libmp3lame',
                '-q:a', '2', output_path
            ], check=True, capture_output=True)
            os.remove(list_file)
            return output_path
        except Exception as e:
            print(f'ffmpeg 合并失败: {e}')
            return None


class GPTSoVITSService(BaseTTSService):
    """GPT-SoVITS 服务"""

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        import requests
        import urllib.parse

        # GPT-SoVITS API 调用
        params = {
            'text': text,
            'text_language': 'zh',
            'refer_wav_path': voice_asset.audio_file.path if voice_asset.audio_file else '',
            'prompt_text': '',
            'prompt_language': 'zh',
        }
        params.update(self.engine.default_params if self.engine else {})
        params.update(kwargs)

        try:
            # 调用本地 GPT-SoVITS API
            url = self.api_url or 'http://127.0.0.1:9880'
            response = requests.get(url, params=params, timeout=300)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return output_path
            else:
                raise Exception(f'API 返回错误: {response.status_code}')
        except Exception as e:
            raise Exception(f'GPT-SoVITS 合成失败: {e}')


class EdgeTTSService(BaseTTSService):
    """Edge TTS 服务（在线，无需GPU）"""

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        try:
            import edge_tts
            import asyncio
            import re

            # 优先从 voice_asset 的 name/tags 中解析 EdgeTTS 音色
            voice = kwargs.get('voice', 'zh-CN-XiaoxiaoNeural')
            if voice_asset:
                search_text = f'{voice_asset.name} {voice_asset.tags or ""}'
                match = re.search(r'zh-[A-Z]{2}-\w+Neural', search_text)
                if match:
                    voice = match.group(0)

            rate = kwargs.get('rate', '+0%')
            volume = kwargs.get('volume', '+0%')

            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(communicate.save(output_path))
            finally:
                loop.close()

            return output_path
        except ImportError:
            raise Exception('edge-tts 未安装，请执行: pip install edge-tts')
        except Exception as e:
            raise Exception(f'Edge TTS 合成失败: {e}')


class IndexTTSService(BaseTTSService):
    """IndexTTS 服务（本地GPU）"""

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        try:
            # 调用 story/multi_speaker_novel.py 中的逻辑
            import sys
            story_path = os.path.join(settings.BASE_DIR.parent, 'story')
            if story_path not in sys.path:
                sys.path.insert(0, story_path)

            from indextts.infer import IndexTTS

            # 这里简化处理，实际应该使用单例模式
            tts = IndexTTS(
                cfg_path=os.path.join(story_path, 'checkpoints', 'config.yaml'),
                model_dir=os.path.join(story_path, 'checkpoints'),
                is_fp16=True,
                device='cuda:0'
            )

            tts.infer(
                audio_prompt=voice_asset.audio_file.path if voice_asset.audio_file else '',
                text=text,
                output_path=output_path,
                verbose=False
            )
            return output_path
        except Exception as e:
            raise Exception(f'IndexTTS 合成失败: {e}')


class XTTSApiService(BaseTTSService):
    """XTTS API 服务"""

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        import requests

        url = self.api_url or 'http://127.0.0.1:8020/tts'
        data = {
            'text': text,
            'speaker_wav': voice_asset.audio_file.path if voice_asset.audio_file else '',
            'language': 'zh',
        }
        data.update(kwargs)

        try:
            response = requests.post(url, json=data, timeout=300)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return output_path
            else:
                raise Exception(f'API 返回错误: {response.status_code}')
        except Exception as e:
            raise Exception(f'XTTS API 合成失败: {e}')


class MockTTSService(BaseTTSService):
    """模拟 TTS 服务（用于测试）"""

    def synthesize(self, text, voice_asset, output_path, **kwargs):
        """生成一个静音音频用于测试"""
        try:
            import numpy as np
            import soundfile as sf

            duration = min(len(text) * 0.3, 30)  # 估算时长
            sample_rate = 24000
            samples = int(duration * sample_rate)
            audio = np.random.randn(samples) * 0.01  # 静音
            sf.write(output_path, audio, sample_rate)
            return output_path
        except ImportError:
            # 如果 soundfile 也没有，创建一个空文件
            Path(output_path).touch()
            return output_path


def get_tts_service(engine_type, engine_config=None):
    """根据引擎类型获取对应的 TTS 服务"""
    services = {
        'gpt_sovits': GPTSoVITSService,
        'edge_tts': EdgeTTSService,
        'indextts': IndexTTSService,
        'xtts': XTTSApiService,
        'mock': MockTTSService,
    }
    service_class = services.get(engine_type, MockTTSService)
    return service_class(engine_config)


def run_tts_generation_task(task_id):
    """执行 TTS 生成任务（用于后台任务队列）"""
    from django.utils import timezone
    from .models import TTSGenerationTask, TTSSegmentResult, VoiceAsset

    try:
        task = TTSGenerationTask.objects.get(id=task_id)
    except TTSGenerationTask.DoesNotExist:
        print(f'任务 {task_id} 不存在')
        return

    task.status = 'generating'
    task.started_at = timezone.now()
    task.save()

    # 创建输出目录
    output_dir = os.path.join(settings.MEDIA_ROOT, 'generated_tts', f'task_{task.id}')
    os.makedirs(output_dir, exist_ok=True)
    task.output_dir = output_dir
    task.save()

    # 获取引擎
    engine = task.engine
    if not engine:
        task.status = 'failed'
        task.error_message = '未配置 TTS 引擎'
        task.save()
        return

    service = get_tts_service(engine.engine_type, engine)
    script_data = task.script_data or []
    speaker_voice_map = task.speaker_voice_map or {}

    task.total_segments = len(script_data)
    task.save()

    # 创建片段结果记录
    segment_results = []
    for i, segment in enumerate(script_data):
        sr = TTSSegmentResult.objects.create(
            task=task,
            sequence_number=i + 1,
            speaker=segment.get('speaker', '旁白'),
            text=segment.get('text', ''),
            emotion=segment.get('emotion', '')
        )
        voice_id = speaker_voice_map.get(segment.get('speaker', '旁白'))
        if voice_id:
            try:
                sr.voice_asset = VoiceAsset.objects.get(id=voice_id)
            except VoiceAsset.DoesNotExist:
                pass
        sr.save()
        segment_results.append(sr)

    # 批量合成
    completed = 0
    failed = 0
    audio_paths = []

    for i, segment in enumerate(script_data):
        sr = segment_results[i]
        sr.status = 'generating'
        sr.save()

        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', '')

        voice_id = speaker_voice_map.get(speaker)
        if not voice_id:
            sr.status = 'failed'
            sr.error_message = f'角色 {speaker} 未配置语音'
            sr.save()
            failed += 1
            continue

        try:
            voice_asset = VoiceAsset.objects.get(id=voice_id)
            output_path = os.path.join(output_dir, f'segment_{i+1:04d}_{speaker}.wav')

            service.synthesize(text, voice_asset, output_path, emotion=emotion)

            sr.audio_file = f'generated_tts/task_{task.id}/segment_{i+1:04d}_{speaker}.wav'
            sr.status = 'completed'
            sr.save()

            audio_paths.append(output_path)
            completed += 1

        except Exception as e:
            sr.status = 'failed'
            sr.error_message = str(e)
            sr.save()
            failed += 1
            task.processing_log += f'\n片段 {i+1} 失败: {e}'

        task.completed_segments = completed
        task.failed_segments = failed
        task.progress = int((i + 1) / len(script_data) * 100)
        task.save()

    # 合并音频
    if audio_paths:
        task.status = 'merging'
        task.save()

        merged_path = os.path.join(output_dir, 'merged_audio.wav')
        result = service.merge_audio(audio_paths, merged_path)
        if result:
            task.merged_audio_path = result

    # 计算总时长
    total_duration = 0
    for sr in segment_results:
        if sr.status == 'completed' and sr.audio_file:
            try:
                import torchaudio
                audio, sr_rate = torchaudio.load(sr.audio_file.path)
                total_duration += audio.shape[-1] / sr_rate
            except:
                pass

    task.total_duration = total_duration
    task.status = 'completed' if failed < len(script_data) else 'failed'
    if failed == len(script_data):
        task.error_message = '所有片段生成失败'
    task.save()
