/** A generated landscape with fine detail, so every tool has something visible to work on. */
export async function makeSampleImage(): Promise<Blob> {
  const w = 1200
  const h = 800
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const g = canvas.getContext('2d')!

  const sky = g.createLinearGradient(0, 0, 0, h * 0.7)
  sky.addColorStop(0, '#27345f')
  sky.addColorStop(0.55, '#c8647a')
  sky.addColorStop(1, '#ffc98a')
  g.fillStyle = sky
  g.fillRect(0, 0, w, h)

  let seed = 7
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)

  g.fillStyle = 'rgba(255,255,255,0.8)'
  for (let i = 0; i < 90; i++) g.fillRect(rand() * w, rand() * h * 0.35, 1 + rand() * 2, 1 + rand() * 2)

  g.fillStyle = '#fff3c9'
  g.beginPath()
  g.arc(w * 0.68, h * 0.5, 74, 0, Math.PI * 2)
  g.fill()

  const ridge = (base: number, amp: number, color: string, wave: number) => {
    g.fillStyle = color
    g.beginPath()
    g.moveTo(0, h)
    for (let x = 0; x <= w; x += 8) {
      g.lineTo(x, base + Math.sin(x / wave) * amp + Math.sin(x / (wave * 0.37)) * amp * 0.4)
    }
    g.lineTo(w, h)
    g.fill()
  }
  ridge(h * 0.58, 46, '#7d4a73', 140)
  ridge(h * 0.68, 38, '#4b3260', 110)
  ridge(h * 0.8, 30, '#241a3d', 90)

  g.fillStyle = '#120d24'
  for (let i = 0; i < 46; i++) {
    const x = rand() * w
    const y = h * 0.82 + rand() * h * 0.16
    const s = 14 + rand() * 30
    g.beginPath()
    g.moveTo(x, y - s * 2)
    g.lineTo(x - s * 0.5, y)
    g.lineTo(x + s * 0.5, y)
    g.fill()
  }

  g.fillStyle = '#f5f2ea'                 // a sharp subject: bold lines show blur and enhance clearly
  g.font = '700 54px "Instrument Sans Variable", sans-serif'
  g.fillText('Sample photo', 56, 104)

  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('Could not create the sample image.'))), 'image/png'),
  )
}
