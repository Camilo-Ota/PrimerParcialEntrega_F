/**
 * Confeti simple en canvas puro (sin dependencias externas).
 * Crea un canvas fijo a pantalla completa, lanza un puñado de partículas
 * de colores que caen con gravedad y rotación, y se autodestruye al terminar.
 */

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  rotation: number
  rotationSpeed: number
  shape: 'rect' | 'circle'
}

const COLORS = ['#22d3ee', '#a3e635', '#facc15', '#fb7185', '#c084fc', '#60a5fa', '#f97316']

export function fireConfetti(durationMs = 2600, particleCount = 160): void {
  const canvas = document.createElement('canvas')
  canvas.style.position = 'fixed'
  canvas.style.inset = '0'
  canvas.style.width = '100vw'
  canvas.style.height = '100vh'
  canvas.style.pointerEvents = 'none'
  canvas.style.zIndex = '9999'
  document.body.appendChild(canvas)

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    canvas.remove()
    return
  }

  const dpr = window.devicePixelRatio || 1
  const resize = () => {
    canvas.width = window.innerWidth * dpr
    canvas.height = window.innerHeight * dpr
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  resize()
  window.addEventListener('resize', resize)

  const width = window.innerWidth
  const particles: Particle[] = Array.from({ length: particleCount }, () => ({
    x: Math.random() * width,
    y: -20 - Math.random() * 200,
    vx: (Math.random() - 0.5) * 4,
    vy: 2 + Math.random() * 3,
    size: 6 + Math.random() * 6,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
    rotation: Math.random() * Math.PI * 2,
    rotationSpeed: (Math.random() - 0.5) * 0.3,
    shape: Math.random() > 0.5 ? 'rect' : 'circle',
  }))

  const gravity = 0.06
  const start = performance.now()
  let rafId = 0

  const cleanup = () => {
    cancelAnimationFrame(rafId)
    window.removeEventListener('resize', resize)
    canvas.remove()
  }

  const tick = (now: number) => {
    const elapsed = now - start
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)

    for (const p of particles) {
      p.vy += gravity
      p.x += p.vx
      p.y += p.vy
      p.rotation += p.rotationSpeed

      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rotation)
      ctx.fillStyle = p.color
      if (p.shape === 'rect') {
        ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2)
      } else {
        ctx.beginPath()
        ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.restore()
    }

    if (elapsed < durationMs) {
      rafId = requestAnimationFrame(tick)
    } else {
      cleanup()
    }
  }

  rafId = requestAnimationFrame(tick)
}
