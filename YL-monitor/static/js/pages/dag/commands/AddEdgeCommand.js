/**
 * 添加连线命令
 * 拆分自: page-dag.js
 * 版本: v1.0.0
 */

export class AddEdgeCommand {
  /**
   * @param {DAGPage} page - DAG页面实例
   * @param {Object} edge - 边线数据 {from, to, label?}
   */
  constructor(page, edge) {
    this.page = page;
    this.edge = { ...edge }; // 深拷贝防止引用问题
  }

  /**
   * 执行添加连线
   */
  execute() {
    // 检查是否已存在相同连线
    const exists = this.page.edges.some(e => 
      e.from === this.edge.from && e.to === this.edge.to
    );
    
    if (!exists) {
      this.page.edges.push(this.edge);
      this.page.renderEdges();
    }
  }

  /**
   * 撤销添加连线
   */
  undo() {
    this.page.edges = this.page.edges.filter(e => 
      !(e.from === this.edge.from && e.to === this.edge.to)
    );
    this.page.renderEdges();
  }

  /**
   * 获取命令描述
   * @returns {string}
   */
  getDescription() {
    const fromNode = this.page.nodes.find(n => n.id === this.edge.from);
    const toNode = this.page.nodes.find(n => n.id === this.edge.to);
    return `添加连线: ${fromNode?.name || this.edge.from} → ${toNode?.name || this.edge.to}`;
  }
}
