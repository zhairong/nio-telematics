# NIO Open Platform for Home Assistant（中文说明）

[English](README.md) | 中文

通过 [NIO 欧洲开放平台](https://open-eu.nio.com/) 在 Home Assistant 中展示你的蔚来车辆信息的只读集成。

仓库地址：[zhairong/nio-telematics](https://github.com/zhairong/nio-telematics)（已公开，MIT 协议，已按 HACS 规范准备）。

## 实体
- **传感器（Sensors）**：电量百分比、续航里程、充电状态、车速、里程表、温度、电池/电芯数据、车窗位置、座椅加热/通风、冰箱、行程、驾驶模式……
- **二元传感器（Binary sensors）**：车门、前舱盖、尾门、充电口、车锁、车灯、空调。
- **设备跟踪器（Device tracker）**：车辆位置（仅在蔚来上报有效定位时更新）。

许多诊断类实体默认处于禁用状态，可在实体注册表中手动启用。
轮询频率：核心数据（电量、车辆状态、位置、车门）每 60 秒一次；其他数据每 5 分钟一次。
实体名称提供英文、简体中文、德文三种翻译，会根据每个用户在 Home Assistant 中设置的语言自动切换。

## 安装

### HACS（推荐）
HACS → ⋮ → **自定义仓库（Custom repositories）** → 添加 `https://github.com/zhairong/nio-telematics`，类别选择 **Integration** → 安装 → 重启 Home Assistant。
（本仓库暂未进入 HACS 默认商店，需要先添加为自定义仓库。）

### 手动安装
1. 下载本仓库（例如 `git clone`，或下载 `main` 分支的 ZIP 压缩包）。
2. 将 `custom_components/nio_open` 复制到 `<你的 HA 配置目录>/custom_components/nio_open`。
3. 重启 Home Assistant，然后按照下方的"配置"步骤操作。请勿将你的凭证或 Home Assistant 配置提交回本仓库。

## 配置
1. 在 NIO 开放平台控制台中，为你的应用注册以下重定向 URI：
   - `https://my.home-assistant.io/redirect/oauth`（推荐；需在 my.home-assistant.io 上设置你的 HA 地址）
   - `http://<你的 HA 主机>:8123/auth/external/callback`（备用方案）
2. 进入 设置 → 设备与服务 → **添加集成 → NIO Open Platform**。按提示输入你的 `client_id` / `client_secret`（应用凭证），在蔚来完成授权后，再输入车辆的 VIN 码。

## 说明
- 申请的权限范围（scopes）：`vehicle:read` 以及动力学、位置、能量、车身、座舱、动力总成、诊断相关的 `:read` 权限。未申请 `vehicle:connectivity:read` 和 `aftersales:read`，因为蔚来会因此将整个授权请求拒绝并返回 `invalid_scope`。
- 对于蔚来尚未采样到的环境/车外/冰箱温度，蔚来会返回 `0`；这些值会被当作缺失数据处理（保留上一次真实读数，否则显示为 `unknown`）。"变更（changes）"类接口只提供最近 60 分钟内的数据，因此这些传感器只有在车辆使用时才会刷新。
- 蔚来只返回近期发生变化的数据，因此静止停放的车辆不会上报新数据。最近一次已知的数值（包括位置）会保存在 Home Assistant 的 `.storage` 中，并在重启后恢复；移除集成时这些数据会被删除。
- 开放平台只提供 `position_status/changes` 这一个位置接口，没有"查询当前位置"的接口。只有车辆位置**实际发生变化**时，蔚来才会推送一条位置记录，所以车辆停着不动时，即使 GPS 信号良好，设备跟踪器也会一直是 `unknown`——这和蔚来 App 的表现不一致，是因为 App 走的是蔚来内部私有接口，本集成无法访问。车辆再次行驶后位置会重新出现。
- 个人蔚来应用无法使用 `client_credentials` 授权方式，必须使用授权码（authorization-code）流程。
- 不要让同一个蔚来应用同时被多个 NIO 集成使用，否则会共用蔚来的速率限制（rate limit）。

## 开发
离线测试已在 Python 3.14.6、Home Assistant 2026.10.2 和 `pytest-homeassistant-custom-component==0.13.373` 环境下验证通过。本版本尚未验证更早版本的 Home Assistant 以及真实车辆授权流程。

```
python3.14 -m venv .venv
.venv/bin/pip install pytest-homeassistant-custom-component==0.13.373
.venv/bin/python -m pytest
```
