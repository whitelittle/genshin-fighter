// This selector was inspected on the actual public comment page.
() => ({
  source: 'miyoushe',
  records: Array.from(document.querySelectorAll('div.tw-relative.tw-w-full.tw-px-4.tw-py-3')).map(e => ({
    text: e.children[1]?.textContent?.trim(), time: e.children[0]?.textContent?.trim(), kind: '主评价'
  })).filter(r => r.text),
  advertised: document.querySelector('h1')?.textContent,
  coverage: document.body.textContent.includes('没有更多了') ? '主评价列表到底；不含楼中楼' : '当前已加载主评价；列表未到底'
})
