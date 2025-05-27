# install
+ 复制该文件夹至`superset-frontend/plugins`
+ 执行`npm install`, 安装依赖
+ 修改`superset-frontend/src/visualizations/presets/MainPreset.js`
```python
import { SupersetPluginChartHelloWorld } from 'superset-plugin-chart-hello-world';
```
+ 增加plugins
```python
new RetentionTableChartPlugin().configure({ key: 'retention-table' }),
```