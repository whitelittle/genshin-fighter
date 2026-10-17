// Read only DOM. Run via the supported browser tool after comments load.
() => {
  const root = document.querySelector('bili-comments');
  if (!root) return {records: [], coverage: '未找到评论容器'};
  const records = [];
  function visit(node) {
    for (const e of node.querySelectorAll('*')) {
      if (e.tagName === 'P' && e.textContent.trim()) {
        records.push({text: e.textContent.trim().replace(/回复\s*[@＠][^:：\n]{1,100}[:：]\s*/g,'回复匿名玩家：'), kind: '页面评论/回复'});
      }
      if (e.shadowRoot) visit(e.shadowRoot);
    }
  }
  if (root.shadowRoot) visit(root.shadowRoot); else visit(root);
  return {source: 'bilibili', records, coverage: '当前已加载的评论与展开回复；未展开分页不计入全量'};
}
