# HangRail

干洗挂衣杆：按衣长一维 First-Fit 上杆，取件释放，逾期扫描。

## 启动

```bash
docker compose up --build
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:4400 |
| API | http://localhost:9400 |
| API 文档 | http://localhost:9400/docs |
| Postgres | localhost:5445 |

健康检查：`GET http://localhost:9400/api/health`

## 页面

- `/stores` — 门店
- `/rails` — 挂杆
- `/orders` — 工单
- `/occupancy` — 占位图
- `/pickup` — 取件
- `/overdue` — 逾期

## 使用说明

1. 查看门店挂杆长度；在挂杆页为每根杆配置相邻衣物间隔缓冲（cm，0 为不缓冲）。
2. 工单上杆按衣长 First-Fit 占位；有缓冲的杆新衣起点至少离开前衣 `end + 缓冲`，新衣与后衣之间同样留出缓冲，杆的两端不加缓冲。贴边空隙因缓冲无法容纳时自动改挂更靠后的空隙/挂杆；全部失败时返回“因缓冲导致空间不足”，与普通无空位区分。
3. 占位图为横向尺线，相邻衣物之间的留白以虚线标出并显示厘米数；取件释放后空隙合并并按缓冲规则重新可入；逾期页扫描清退。

## 开发与测试

```bash
docker compose exec api pytest -q
```
