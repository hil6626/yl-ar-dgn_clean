# systemd

本目录提供 `YL-monitor` 的 systemd 服务示例，用于在 Linux 服务器/工作站上后台守护与开机自启。

## 安装（示例）

1) 复制服务文件：

```bash
sudo cp systemd/yl-monitor.service /etc/systemd/system/yl-monitor.service
```

2) 修改 `WorkingDirectory` 与 `ExecStart` 中的路径（指向你的仓库目录与 venv）。
   - 端口与 host 默认读取 `.env` 的 `YL_MONITOR_PORT` / `YL_MONITOR_HOST`（未配置则回退到 5500 / 0.0.0.0）

3) 启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now yl-monitor
sudo systemctl status yl-monitor
```

4) 查看日志：

```bash
journalctl -u yl-monitor -f
```
