---
name: web-admin-app-permissions
description: >
  在 Web 管理后台中自动化创建应用并配置权限树。
  当用户说"打开某个网站，用账号密码登录，帮我创建一个应用并配置权限"、
  "找到 xx 应用，按这个表格帮我配置权限"、"帮我在后台批量创建权限节点"时，
  必须使用本 skill。适用于基于 Element UI + vxe-table 的企业管理后台。
  同时适用于仅配置权限（已有应用）和从头创建应用+权限两种场景。
allowed-tools: Bash(playwright-cli:*)
---

# Web 管理后台：创建应用 & 配置权限树

## 使用前提

开始前，从对话中确认以下信息（缺少时直接询问用户，不要猜测）：
1. **环境 / URL**：用户说"测试"/"预发"/"线上"时直接套用下方已知地址表；也可直接给 URL
2. **账号 / 密码**：可以是对话中直接说的，也可以是文件路径（如 `playwright/account.md`）
3. **权限配置**：图片、表格、文字均可；图片用 `view_image` 读取
4. **应用名称**：新建时需填完整信息；已有应用时只需名称

---

## 已知环境地址

| 环境 | 登录入口 | 权限管理页 |
|------|----------|-----------|
| 测试 | `https://testobworkwx.hnlshm.com/login` | `/user-center/system/resource/resource` |
| 预发 | `https://pre-portal.hnlshm.com/login` | `/user-center/system/resource/resource` |
| 线上 | `https://portal.hnlshm.com/login` | `/user-center/system/resource/resource` |

其他站点路径需通过 snapshot 确认后再执行。

---

## 执行原则：减少冗余 snapshot

- **已知路径直接 goto**，不需要先 snapshot 探索导航菜单
- **已知选择器直接 eval 操作**，不需要先 snapshot 再找 ref
- **只在以下情况 snapshot**：首次打开页面验证登录状态、出现意外、需要找某个不确定的 ref
- 对话框填写字段用 placeholder / label 定位，无需 ref

---

## 第一步：登录

**始终使用 `--headed --persistent` 打开浏览器**，保证有界面可见、会话持久化：

```bash
playwright-cli open <登录URL> --headed --persistent
# 直接用 placeholder 定位，无需 snapshot 找 ref
playwright-cli fill "getByPlaceholder('请输入账号')" "账号"
playwright-cli fill "getByPlaceholder('请输入密码')" "密码"
playwright-cli click "getByText('登录')"
playwright-cli snapshot  # 唯一一次 snapshot：确认是否登录成功
```

**验证点**：快照中出现侧边导航菜单或用户名，则登录成功；仍在登录页则检查账号密码。

**Session 过期处理**（XHR 返回 401 时）：
```bash
playwright-cli goto <登录URL>
playwright-cli fill "getByPlaceholder('请输入账号')" "账号"
playwright-cli fill "getByPlaceholder('请输入密码')" "密码"
playwright-cli click "getByText('登录')"
# 重新 goto 权限页，继续未完成的节点
```

---

## 第二步（可选）：新建应用

仅当用户要求创建新应用时执行。直接 goto 应用管理页：

> 注意：三个环境的应用管理路径实测为 `/user-center/system/microAppManagement/index`，
> 不是 `/user-center/system/app/app`。

```bash
playwright-cli goto <baseURL>/user-center/system/microAppManagement/index
playwright-cli snapshot  # 确认页面结构（首次访问）
playwright-cli click "getByText('新增')"
playwright-cli fill "getByPlaceholder('请输入应用名称')" "应用名称"
playwright-cli fill "getByPlaceholder('请输入应用编码')" "com-xxx-yyy"
# 其他字段按需填写，提交
playwright-cli click "getByText('提交')"
```

---

## 第三步：进入权限配置页 + 安装拦截器

两步合一，直接执行：

```bash
playwright-cli goto <权限管理页URL>
# 立即安装 XHR 拦截器，无需 snapshot
playwright-cli eval "(window._xhrOpen=XMLHttpRequest.prototype.open,window._xhrSend=XMLHttpRequest.prototype.send,XMLHttpRequest.prototype.open=function(m,u){this._url=u;return window._xhrOpen.apply(this,arguments)},XMLHttpRequest.prototype.send=function(d){var xhr=this;xhr.addEventListener('load',function(){if(xhr._url&&xhr._url.indexOf('resource/add')>-1){window._xhrResp=xhr.responseText}});return window._xhrSend.apply(this,arguments)},'xhrok')"
```

**拦截器作用**：每次提交后可读取接口真实结果，因为对话框不展示后端错误信息。

---

## 第四步：过滤目标应用

每次（包括每个节点创建之前）都需要重新过滤，因为提交成功后过滤器会自动重置：

```bash
# 一次 eval 完成：打开下拉 → 选中目标应用
playwright-cli eval "document.querySelector('.el-select').click()"
playwright-cli eval "Array.from(document.querySelectorAll('.el-select-dropdown__item')).find(e=>e.textContent.trim()==='目标应用名').click()"
# 点击查询
playwright-cli eval "Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='查询').click()"
playwright-cli snapshot  # 确认筛选结果
```

---

## 第五步：展开权限树

vxe-table 树**只展开当前层**，必须逐层顺序点击，不能 forEach 批量：

```bash
# 展开根节点（第 0 个展开按钮）
playwright-cli eval "document.querySelectorAll('.vxe-cell--tree-btn')[0].click()"
# 展开目标二级节点（按需，根据目标父节点的顺序 index）
playwright-cli eval "document.querySelectorAll('.vxe-cell--tree-btn')[1].click()"
# 展开三级节点（如需要）
playwright-cli eval "document.querySelectorAll('.vxe-cell--tree-btn')[2].click()"
playwright-cli snapshot  # 确认目标父节点行已出现
```

> **index 规则**：按照树节点的展示顺序，从上到下 0-based 编号。每次重新过滤后都从 [0] 开始。

---

## 第六步：触发新增弹窗

用行文字定位，不依赖 ref，直接 eval 点击：

```bash
# 对根节点新增下级（只有"新增下级"按钮的行）
playwright-cli eval "Array.from(document.querySelectorAll('tr')).find(tr=>tr.innerText.replace(/\\s+/g,'')===tr.innerText.replace(/\\s+/g,'')&&tr.querySelectorAll('button').length===1&&tr.querySelector('button').textContent.trim()==='新增下级').querySelector('button').click()"

# 对二级目录新增下级（有"新增下级 新增同级 编辑 删除"的行，取第 N 个）
playwright-cli eval "Array.from(document.querySelectorAll('tr')).filter(tr=>{var t=tr.innerText.replace(/\\s+/g,'');return t.includes('新增下级')&&t.includes('新增同级')})[N].querySelectorAll('button')[0].click()"

# 对功能按钮行新增同级（无"新增下级"，有"新增同级 编辑 删除"）
playwright-cli eval "Array.from(document.querySelectorAll('tr')).filter(tr=>{var t=tr.innerText.replace(/\\s+/g,'');return !t.includes('新增下级')&&t.includes('新增同级')})[N].querySelector('button').click()"
```

---

## 第七步：填写并提交表单

弹窗已知字段结构，直接填写无需额外 snapshot：

```bash
# 填写名称（对话框第一个输入框）
playwright-cli fill "getByPlaceholder('请输入菜单名称')" "权限名称"
# 填写编码
playwright-cli fill "getByPlaceholder('请输入菜单编码')" "PERMISSION_CODE"

# 选择类型：目录 or 功能按钮
playwright-cli eval "Array.from(document.querySelectorAll('.el-dialog .el-select')).find(s=>s.textContent.includes('目录')||s.textContent.includes('菜单类型')).click()"
playwright-cli eval "Array.from(document.querySelectorAll('.el-select-dropdown__item')).find(e=>e.textContent.trim()==='功能按钮').click()"

# 若类型为"功能按钮"，填写菜单路径（目录类型跳过此步）
playwright-cli fill "getByPlaceholder('请输入菜单路径')" "/module/path"

# 提交
playwright-cli eval "Array.from(document.querySelectorAll('.el-dialog button')).find(b=>b.textContent.trim()==='提交').click()"

# 检查结果
playwright-cli eval "JSON.stringify(window._xhrResp)"
```

**结果判断**：
- `"respCode":"200"` → 成功，继续下一个节点
- `"ARGS_ILLEGAL"` + 编码重复 → 节点已存在，用取消关闭弹窗，跳过
- `undefined` → 拦截器丢失（页面刷新过），重新安装（第三步）

**关闭失败弹窗**：
```bash
playwright-cli eval "Array.from(document.querySelectorAll('.el-dialog button')).find(b=>b.textContent.trim()==='取消').click()"
```

---

## 第八步：循环直到所有节点完成

每个节点按以下顺序执行（已知流程，跳过不必要探索）：

```
重新过滤（第四步）→ 展开树（第五步）→ 触发弹窗（第六步）→ 填写提交（第七步）→ 确认结果
```

**创建顺序必须从高层级到低层级**：父节点必须在子节点之前创建。

---

## 权限配置输入格式

用户可以提供以下任意形式，处理方式如下：

| 输入形式 | 处理方式 |
|---------|--------|
| 图片 | 用 `view_image` 读取，提取出节点表格 |
| Markdown 表格 | 直接解析 |
| 文字描述 | 解析为节点列表，确认后执行 |
| 账号在对话中 | 直接使用 |
| 账号在文件中 | 用 `read_file` 读取文件 |

**标准节点格式**：

| 节点名称 | 编码 | 类型 | 层级 | 父节点 | 菜单路径 |
|---------|------|------|------|--------|---------|
| 首页 | HOME | 目录 | 2 | 应用根节点 | — |
| 消息权限 | HOME_MESSAGE | 功能按钮 | 3 | 首页 | /home/message |
| 我的 | MY | 目录 | 2 | 应用根节点 | — |
| 个人资料 | MY_PROFILE | 功能按钮 | 3 | 我的 | /my/profile |

---

## 调试命令（仅在卡住时使用）

```bash
# 查看树展开按钮数（判断展开到第几层）
playwright-cli eval "document.querySelectorAll('.vxe-cell--tree-btn').length"

# 列出所有包含操作按钮的行内容（行定位调试）
playwright-cli eval "Array.from(document.querySelectorAll('tr')).map(tr=>tr.innerText.replace(/\\s+/g,' ').trim()).filter(t=>t.includes('新增')).join('\\n')"

# 查看最后一次接口返回
playwright-cli eval "JSON.stringify(window._xhrResp)"

# 检查弹窗是否打开
playwright-cli eval "!!document.querySelector('.el-dialog__wrapper:not([style*=none])')"
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 对话框提交后不关闭 | 接口错误（编码重复等），UI 无提示 | 检查 `window._xhrResp`，eval 点击"取消" |
| eval 找不到按钮 | 树未展开到目标层级 | 逐层点击 `.vxe-cell--tree-btn` |
| 过滤器选项为空 | 下拉列表未加载 | 稍等后重新 eval click 下拉框 |
| 菜单路径字段不出现 | 类型未选为"功能按钮" | 先选类型，等 DOM 更新后再填路径 |
| `window._xhrResp` 为 undefined | 页面跳转/刷新后拦截器丢失 | 重新执行第三步安装命令 |
| 401 / Session 过期 | Token 失效 | 重新登录（第一步），goto 回权限页继续 |
| getByPlaceholder 找不到元素 | placeholder 文字不同 | snapshot 一次确认实际 placeholder 文字 |
