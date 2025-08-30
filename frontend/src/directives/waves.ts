// 简单的波纹效果指令
export const waves = {
  mounted(el: HTMLElement) {
    el.addEventListener('click', (e: MouseEvent) => {
      const rect = el.getBoundingClientRect()
      const ripple = document.createElement('span')
      const size = Math.max(rect.width, rect.height)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2
      
      ripple.style.width = ripple.style.height = size + 'px'
      ripple.style.left = x + 'px'
      ripple.style.top = y + 'px'
      ripple.classList.add('ripple')
      
      el.appendChild(ripple)
      
      setTimeout(() => {
        ripple.remove()
      }, 600)
    })
  }
}
