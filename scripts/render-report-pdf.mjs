import { spawn } from 'node:child_process'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const output = process.argv[2]
if (!output) throw new Error('Usage: node scripts/render-report-pdf.mjs output/pdf/vyaparsathi-report.pdf')

const profile = await mkdtemp(join(tmpdir(), 'vyaparsathi-pdf-'))
const child = spawn(chrome, ['--headless=new', '--disable-gpu', '--no-first-run', `--user-data-dir=${profile}`, '--remote-debugging-port=0', 'http://127.0.0.1:5173/'], { stdio: 'ignore' })

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const getJson = async (url) => {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Request failed: ${response.status} ${url}`)
  return response.json()
}

try {
  let port
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const activePort = await readFile(join(profile, 'DevToolsActivePort'), 'utf8')
      port = activePort.split('\n')[0]
      break
    } catch {
      await wait(100)
    }
  }
  if (!port) throw new Error('Chrome DevTools endpoint did not start')

  const targets = await getJson(`http://127.0.0.1:${port}/json/list`)
  const target = targets.find((item) => item.type === 'page')
  if (!target?.webSocketDebuggerUrl) throw new Error('No report-rendering page was available')

  const socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  let requestId = 0
  const calls = new Map()
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    const pending = calls.get(message.id)
    if (!pending) return
    calls.delete(message.id)
    if (message.error) pending.reject(new Error(message.error.message))
    else pending.resolve(message.result)
  })
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++requestId
    calls.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
  const evaluate = (expression) => call('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })

  await call('Page.enable')
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const ready = await evaluate("document.querySelectorAll('button').length > 0")
    if (ready.result?.value) break
    await wait(100)
  }
  await evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('Start business assessment'))?.click()")
  await wait(150)
  await evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.trim() === 'Full report')?.click()")
  await wait(300)
  const state = await evaluate("({ reportReady: Boolean(document.querySelector('.report-page')), excludedMapNodes: document.querySelectorAll('[data-pdf-exclude=\"true\"]').length, hasMapText: document.body.innerText.includes('Geographic view unavailable') })")
  if (!state.result?.value?.reportReady || !state.result.value.excludedMapNodes) throw new Error('The report or its PDF exclusions did not render')

  const pdf = await call('Page.printToPDF', { format: 'A4', printBackground: true, preferCSSPageSize: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 })
  await writeFile(output, Buffer.from(pdf.data, 'base64'))
  socket.close()
  process.stdout.write(`${JSON.stringify(state.result.value)}\n`)
} finally {
  if (child.exitCode === null) {
    child.kill('SIGTERM')
    await new Promise((resolve) => child.once('exit', resolve))
  }
  await rm(profile, { recursive: true, force: true })
}
