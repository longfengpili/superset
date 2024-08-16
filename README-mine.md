<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Superset

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/apache/superset?sort=semver)](https://github.com/apache/superset/tree/latest)
[![Build Status](https://github.com/apache/superset/workflows/Python/badge.svg)](https://github.com/apache/superset/actions)
[![PyPI version](https://badge.fury.io/py/apache-superset.svg)](https://badge.fury.io/py/apache-superset)
[![Coverage Status](https://codecov.io/github/apache/superset/coverage.svg?branch=master)](https://codecov.io/github/apache/superset)
[![PyPI](https://img.shields.io/pypi/pyversions/apache-superset.svg?maxAge=2592000)](https://pypi.python.org/pypi/apache-superset)
[![Get on Slack](https://img.shields.io/badge/slack-join-orange.svg)](http://bit.ly/join-superset-slack)
[![Documentation](https://img.shields.io/badge/docs-apache.org-blue.svg)](https://superset.apache.org)

<picture width="500">
  <source
    media="(prefers-color-scheme: dark)"
    src="https://github.com/apache/superset/raw/master/superset-frontend/src/assets/branding/superset-logo-horiz-apache-dark.png"
    alt="Superset logo (dark)"
  />
  <img
    src="https://github.com/apache/superset/raw/master/superset-frontend/src/assets/branding/superset-logo-horiz-apache.png"
    alt="Superset logo (light)"
  />
</picture>

A modern, enterprise-ready business intelligence web application.

## Questions
**1. 增加中文**  
在`./docker/pythonpath_dev/superset_config.py`中增加配置内容。
```python
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'},
    'zh': {'flag': 'cn', 'name': '中文'},
}
```
**2. load examples**  
+ 在hosts增加对应的内容。
```bash
echo '20.205.243.166 github.com' >> /etc/hosts
superset load-examples
```  
+ docker-compose中添加hosts
```yaml
extra_hosts:
  - "github.com:20.205.243.166"
  - "deb.debian.org:151.101.110.132"
```

**3. trino 数据库连接**
+ 安装trino库
```bash
pip install trino
```
+ 配置sqlalchemy uri
```bash
trino://username:password@trino.sincetimes.com:8443/hive
```

**4. sql增加时间参数**
+ 在参数中增加配置
```
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING ': True,
}
```
+ sql使用例子
```sql
with user_daily as(
select
date, part_date,
role_id,
level_min as level_min_daily, level_max as level_max_daily,
viplevel_min as viplevel_min_daily, viplevel_max as viplevel_max_daily,
money as money_daily,
money_rmb as money_rmb_daily, exchange_rate
from hive.warship_jp_w.dws_user_daily_di05
where part_date >= '{{ from_dttm[:10] ro '2023-12-01' }}'
and part_date <= '{{ to_dttm[:10] or'2023-12-07' }}'
),

user_daily_info as
(select
a.date, a.part_date,
a.role_id,
a.level_min_daily, a.level_max_daily,
a.viplevel_min_daily, a.viplevel_max_daily,
a.money_daily, a.money_rmb_daily, a.exchange_rate,
b.install_date, date(b.lastlogin_ts) as lastlogin_date,
b.moneyrmb_ac, b.firstpay_date, b.firstpay_goodid, b.firstpay_level,
b.zone_id, b.channel,
date_diff('day', b.install_date, a.date) as retention_day,
date_diff('day', firstpay_date, a.date) as pay_retention_day,
date_diff('day', b.install_date, firstpay_date) as firstpay_interval_days
from user_daily a
left join hive.warship_jp_w.dws_user_info_df05 b
on a.role_id = b.role_id
)

select *
from user_daily_info
```

**5. superset-frontend编译错误**
```
npm WARN ERESOLVE overriding peer dependency
npm ERR! code ENOTEMPTY
npm ERR! syscall rename
npm ERR! path /app/superset-frontend/plugins/plugin-chart-handlebars/node_modules/jest
npm ERR! dest /app/superset-frontend/plugins/plugin-chart-handlebars/node_modules/.jest-skbXcIUg
npm ERR! errno -39
npm ERR! ENOTEMPTY: directory not empty, rename '/app/superset-frontend/plugins/plugin-chart-handlebars/node_modules/jest' -> '/app/superset-frontend/plugins/plugin-chart-handlebars/node_modules/.jest-skbXcIUg'
```
+ 删除/app/superset-frontend/plugins/plugin-chart-handlebars/node_modules

**6. 批量删除node_modules**
```
find /app/superset-frontend -name "node_modules" -type d -prune -exec rm -rf '{}' +
```

**7. 编译前端**
```
docker-compose -f docker-compose-company.yml superset-node up -d
docker-compose exec -it superset-node bash
cd /app/superset-frontend
npm install
```


**8. 修改sql模板**
+ 文件路径`superset\jinja_context.py`
```python
def process_template(self, sql: str, **kwargs: Any) -> str:
    """Processes a sql template

    >>> sql = "SELECT '{{ datetime(2017, 1, 1).isoformat() }}'"
    >>> process_template(sql)
    "SELECT '2017-01-01T00:00:00'"
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"==502=={sql}")

    def check_dttm(context):
        from datetime import date, timedelta
        today = date.today()
        stoday = today.strftime('%Y-%m-%d')
        syesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        from_dttm = context.get('from_dttm')
        logger.info(f"======{from_dttm}, {context}")
        if not from_dttm:
            context['from_dttm'] = syesterday
            context['to_dttm'] = stoday
            logger.info(f"update from_dttm to {syesterday}, to_dttm to {stoday}")
        return context

    template = self.env.from_string(sql)
    kwargs.update(self._context)

    context = validate_template_context(self.engine, kwargs)
    check_dttm(context)
    # logger.info(context.get('get_filters'))
    return template.render(context)

```

** 8. 自定义jinja函数及调用 **
```python
from datetime import datetime, timedelta
def custom_dttm(dttm: str, default: str = None, shift: int = 0):
    if dttm or default:
        dttm = dttm or default
        dttm = dttm[:10]
    else:
        dttm = (datetime.today() + timedelta(days=shift)).strftime('%Y-%m-%d')
    return dttm

def custom_in(filters: list, *default: tuple[str,]):
    if not filters:
        filters = default

    return "'" + "', '".join(filters) + "'"


JINJA_CONTEXT_ADDONS = {
    'custom_dttm': custom_dttm,
    'custom_in': custom_in,
}
```
```sql
SELECT *
from public.birth_names 
where ds >= '{{ custom_dttm(from_dttm, shift=0) }}'
and name in (
    {{ custom_in(filter_values('name'), 'Aaron', 'Abigail')  }}
)
limit 10
```