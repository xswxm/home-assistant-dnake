# 狄耐克门禁系统（Dnake） Home Assistant (HA) 集成

通过HA集成接入Dnake后可以实现远程控制门禁开启和电梯、监听室内机呼叫并推送等功能。

<a href="demo"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/demo.gif?raw=true" width="450" ></a>

**注意：切勿利用本教程破坏互联网安全，影响居民生活。**

---

# 方案介绍

共提供两种方案，具体如下。

### 1. 方案区别

| 编号    | 主要设备   | 功能区别 | 成本与复杂度 |
| ------ | ----------- | ----------- | ----------- |
| 方案1   | Openwrt路由器 x 1<br>交换机 x 1| 门禁控制: HA 实现<br>直播拉流: HA 实现<br>呼叫接听: 室内机实现 | 成本: 较高<br>复杂度: 高 |
| 方案2   | 小米R1CL路由器 x 1 | 门禁控制: Openwrt 实现<br>直播拉流: HA实现 (待验证)<br>呼叫接听: Openwrt 实现 | 成本: 低<br>复杂度: 低 |

### 2、HA 与 米家功能区别

| 编号    |  HA  | 米家 |
| ------ | ----------- | ----------- |
|  门禁控制  | 支持 | 支持 (通过 巴法云 间接支持)  |
|  视频直播  | 支持 | 暂不支持  |
|  呼叫推送  | 支持 (需要内网穿透以及独立域名)| 暂不支持 |

---

# 安装方式

## 一、配置室内机

### 1. 获取室内机信息

室内机进入 **设置 -> 网络设置**（默认密码一般为`123456`），获取IP地址、子网掩码、默认网关和服务器相关信息。

<a href="Dnake网络设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/1_dnake_network.png?raw=true" width="450" ></a>

室内机进入 **设置 -> 房号设置** 获取栋号、单元和房号。

<a href="Dnake房间设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/1_dnake_room.png?raw=true" width="450" ></a>

---

## 二、配置网络

请根据不同方案进行对应配置

### 方案1

#### 1. 网络拓扑

由于室内机与服务器和室外机在同一个网络，可以在室内机前增加一台交换机，并将原有连接室内机的网线、室内机、和OpenWrt路由器连接至同一个交换机。

<a href="网络拓扑"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m1_structure.png?raw=true" width="450" ></a>

#### 2. 配置OpenWrt

进入 **OpenWrt -> 网络 -> 接口 -> 添加端口**，增加端口配置：
  
- 端口：选择您实际使用的物理网口，如 **eth1**
- 协议：**静态IP**
- IPv4地址：参考之前室内机的IP和网段，填入一个不会引起冲突的IP地址
- IPv4子网掩码：参考室内机填写
- IPv4网关：参考室内机填写
- IPv4广播：留空
- DNS服务器：参考室内机填写
- 其他注意实现：不要启用DHCP和IPv6相关功能，注意配置防火墙

进入 **OpenWrt -> 网络 -> 静态路由**，增加静态路由配置：
  
- 接口：**lan**
- 对象：填Dnake网络的网段，如 **172.16.0.0**
- IPv4子网掩码：填室内机的 **子网掩码**
- IPv4网关：填您设置的 **并网IP**
- 跃迁点：比默认0大即可

成功配置后，路由器下设备可以`ping`通室内机。

---

#### 3. 配置端口转发

参考以下配置两个端口（具体端口视实际情况而定）：

- **Dnake消息服务器端口**：映射到局域网中的HA主机（例如`30884`映射到`192.168.1.10`）。
- **内网HTTP Server端口**：映射到内网PC主机（例如`8080`）。

#### 4. 安装室内机客户端

首先在PC端安装Python环境后运行以下命令启动HTTP服务：

```bash
python -m http.server 8080
```

打开终端（如CMD），通过Telnet连接室内机（注意将 **172.16.1.111** 替换成您的室内机IP）：

```bash
telnet 172.16.1.111 9900
```

如果提示Telnet不可用，请在 **控制面板 -> 程序 -> 启用或关闭Windows功能** 中启用Telnet功能。

telnet连接室内机后，逐条运行以下命令（注意将 **172.16.1.233** 替换成您的室内机IP）：

```bash
# 复制客户端
cd /dnake/data
/dnake/bin/curl http://172.16.1.233:8080/sip_monitor -o sip_monitor

# 修改可执行权限
chmod 755 sip_monitor

# 编辑自启动文件
vi ex_init.sh
```

- **ex_init.sh文件内容：**

```bash
#!/system/bin/sh
/dnake/data/sip_monitor 172.16.1.233:30884 &
```

- 编辑完成后运行以下命令检查程序是否可以正常运行（注意将 **172.16.1.233** 替换成您的室内机IP）：

```bash
/dnake/data/sip_monitor 172.16.1.233:30884
```

如果正常，运行 `reboot` 重启室内机。

> **提示:** <br>a. 因为Dnake室内机有多个不同的平台，如果运行异常，请尝试另一个版本 **sip_monitor_armv7l** (同时需要**tcpdump**)，请将其拷贝到室内机后添加可执行权限后再尝试运行<br>b. 如果flash空间不足，建议拷贝至 **/tmp** 目录下运行，但这样实现开机自启就会比较复杂，可能每次重启都需要手动下载一遍，除非自己额外部署http服务，通过脚本实现每次开机自动下载可执行文件。

---

### 方案2

#### 1. 网络拓扑

<a href="网络拓扑"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_structure.png?raw=true" width="450" ></a>

#### 2. 刷入OpenWrt固件

网上有很多 **小米R1CL** 进ssh刷 Breed 的教程，这里不做展开描述，注意备份数据即可。

输入 `Breed` 后，电脑网线连接路由器的默认 `WAN口`（蓝色端口），按住 **小米R1CL** Reset 按键插电，设备会自动进入 `Breed`。访问 `192.168.1.1`选择定制固件并刷入，注意核对下MD5，防止文件下载错误。

<a href="刷机"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_flash.png?raw=true" width="450" ></a>

#### 2. 连接WiFi

由于默认系统关闭了dhcp等功能，需要手动设置电脑网卡 ip 为 `192.168.5.x` 网段才能访问到刚刷入的 OpenWrt 系统。

<a href="固定IP"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_fixed_ip.png?raw=true" width="450" ></a>

小米R1CL 重启后等待蓝灯亮起，浏览器输入 `192.168.5.1` 即可访问 OpenWrt（默认密码`password`），然后进入 **网络 -> 无线**，设置您的 **WiFi 名称** 和 **WiFi密码**，保存后并应用即可。

<a href="AP设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_ap.png?raw=true" width="450" ></a>

<a href="AP设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_ap2.png?raw=true" width="450" ></a>

<a href="AP设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_ap3.png?raw=true" width="450" ></a>

连上网后就可以把连电脑的网线拔了，后续可以直接输入 **小米R1CL** 无线获取到的ip地址即可访问系统。

#### 3. 连接网线

将门禁室内机原来的网线插入 **小米R1CL** 中间的 `LAN口`，然后再用一根短一点的网线连接室内机和 **小米R1CL** 的另一个 `LAN口`。

<a href="连接网络"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_connection.png?raw=true" width="450" ></a>

#### 4. 配置网络

**小米R1CL** 进入到 **网络 -> 端口 -> doorlink**，参考之前室内机的IP和网段，填入一个不会引起冲突的IP地址和网段（默认为 `172.16.0.201`）。

<a href="接口设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_interface.png?raw=true" width="450" ></a>

进入到 **网络 -> 路由 -> 编辑**，将原来的 `172.16.0.201` 修改为刚才填入的IP和网段，同时按需修改对应网段。

<a href="静态路由设置"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_route.png?raw=true" width="450" ></a>

进入到 **网络 -> 网络诊断 -> IPv4 Ping**，填入室内机的IP，看`ping`是否通畅；此外，室内机上也查看下监控视频，如果都没有问题则继续。

<a href="ping测试"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_op_ping.png?raw=true" width="450" ></a>

#### 5. 软件配置

**小米R1CL** 进入到 **服务 -> 门禁助手**，参考以下配置：

**通用设置**
- 品牌：目前仅支持 `狄耐克`
- 激活码：请私信公众号`hadiy`获取
- 启用服务：一般勾上，开机自启
- 运行状态：显示当前程序的运行状态

**Home Assistant**
- IP地址：HA的IP，呼叫推送需要
- 服务端口：服务端口，默认`30884`

**巴法云**：米家控制需要
- 私钥：请注册 [巴法云](https://cloud.bemfa.com/) 后在 [控制台](https://cloud.bemfa.com/tcp/index.html) 获取，默认为空时不启用该服务
- 室内机SIP信息：如: 10011201@172.16.10.121:5060
- 室外机SIP信息：如: 10019901@172.16.1.101:5060
- 电梯ID：0为所有电梯，1、2、3对应具体电梯编号
- 家庭ID：一般为1

**SIP信息拼接规则**：以 `10011201@172.16.10.121:5060` 为例，可以拆解为 `10 01 12 01 @ 172.16.10.121 : 5060` 这几部分。
- 第一个`10`：栋号
- 第二个`01`：1单元，同理2单元就是02
- 第三个`12`：12楼
- 第四个`01`：室
- 中间的`172.16.10.121`：您室内机的`ip地址`
- 最后的`5060`：SIP端口，默认`5060`

请输入**激活码**，并按需配置**Home Assistant**或**巴法云**，点击 **保存并应用**，此时程序应该显示`运行中`，同时如果有配置`巴法云`，对应 [控制台](https://cloud.bemfa.com/tcp/index.html) 会显示新增的订阅主题并显示在线。

> **提示:** 如果不知道SIP信息，可以默认留空，程序正常运行后，使用室外机呼叫下室内机，正常情况下程序会自动刷新SIP信息。

#### 6. 供电方案

由于`小米R1CL`使用的5V供电，而一般室内机使用的12V电压，所以可能需要借助DC降压模块将电压将12V降压至5V，网上有很多线程的模块，买来简单手动改装下即可。

还有一种方案就是修改电路，主板上有一颗丝印为`WB5HN`的芯片，猜测可能是一个LDO芯片，将5V转成3.3V，可能可以找到12V转3.3V平替的降压芯片？

<a href="供电方案"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/2m2_power_supply.png?raw=true" width="450" ></a>

---

## 四、HA接入

### 1. 安装并配置HA集成

#### 安装集成

将集成（`dnake`文件夹）通过FTP或Samba复制到HA的`/config/custom_components`目录，并重启HA。

#### 配置集成

进入 **HA -> 设置 -> 添加集成**，搜索`dnake`并开始配置以下信息：

- 栋号、单元、房号、室内机IP地址：填入之前室内机上获取的相关信息。
- 家庭ID：默认为1
- 电梯ID：0为所有电梯，1、2、3对应具体电梯编号
- OpenWrt地址：如果使用了方案2，需要填入对应设备的地址，注意需要全称带端口（默认`8080`端口），如 `http:\\192.168.1.100:8080`
- 呼叫监听端口：默认为30884
- 室外机设备：可不填，格式可参考`{"20007": "172.16.0.252"}`。
- 直播流支持：如果视频流或报错有异常请取消勾选。
- MQTT支持：可配置MQTT服务以增加可玩性。

> **直播流提示:**<br>如果使用的方案2，HA将无法直接访问直播流，您可以尝试在HA或者路由器上增加路由解决。<br>如果网络通常，但无法正常添加直播流，也可能时密码错误导致，建议HA配置时关闭直播流。

### 2. 常规功能

- **门禁控制**：选择门禁设备后，点击打开门禁。
- **电梯控制**：选择门禁设备后，点击对应电梯操作。
- **视频预览**：显示每个门禁设备的预览图像（如果启用了 `直播流支持`）。
- **最新事件**：查看最近执行的事件详情。

### 2. 服务调用

进入 **开发者工具 -> 服务**，搜索`dnake`查看支持的服务（如`appoint`、`permit`、`unlock`）。

### 3. 自动化与消息推送

在手机上安装 **Home Assistant** App并完成配置（如果需要不在家里时也能控制设备，请准备好内网穿透），在HA **设置 - 自动化与场景** 中 **创建自动化**，可以自行DIY实现想要的功能。

以下是一个室内机呼叫推送通知示例（YAML格式，请将 **10011001** 替换成自己的集成条目名称）：

```yaml
alias: Dnake室内机呼叫推送通知
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.10011001_last_event
    attribute: time
conditions:
  - condition: state
    entity_id: sensor.10011001_last_event
    attribute: event
    state: ring
actions:
  - data:
      title: >-
        {{ state_attr('camera.dnake_' + state_attr('sensor.10011001_last_event',
        'src_id'), 'friendly_name') or state_attr('sensor.10011001_last_event',
        'src_id') }}
      message: 有人呼叫室内机，请应答。
      data:
        entity_id: >-
          {{ 'camera.dnake_' + state_attr('sensor.10011001_last_event', 'src_id') }}
        actions:
          - action: EXECUTE_DNAKE
            title: 开放通行
          - action: URI
            title: 查看详情
            uri: /config/devices/device/734100ba2c12b66c70d56f145d186ee5
    action: notify.mobile_app_adon
  - wait_for_trigger:
      - event_type: mobile_app_notification_action
        event_data:
          action: EXECUTE_DNAKE
        trigger: event
    timeout: 30
    continue_on_timeout: false
  - action: dnake.unlock
    metadata: {}
    data:
      dst_id: "{{ state_attr('sensor.10011001_last_event', 'src_id') }}"
      dst_ip: "{{ state_attr('sensor.10011001_last_event', 'src_ip') }}"
  - action: dnake.permit
    metadata: {}
    data:
      dst_ip: "{{ state_attr('sensor.10011001_last_event', 'src_ip') }}"
      dst_id: "{{ state_attr('sensor.10011001_last_event', 'src_id') }}"
mode: queued
```

---

## 五、米家接入

### 1. 设备名称修改

`OpenWrt`侧的`门禁助手`程序会自动向巴法云平台添加订阅频道，且都设置了默认昵称。如果不符合期望，可以进入 [控制台](https://cloud.bemfa.com/tcp/index.html) 点击 `更多设置` 修改昵称。

<a href="巴法云"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/doc/5_bemfa.png?raw=true" width="450" ></a>

### 1. 连接巴法云平台

进入 **米家App -> 我的 -> 连接其他平台 -> 添加**，选择 `巴法`，输入您的账号密码关联米家并同步 `巴法云` 上的订阅频道。

### 2. 使用小爱音响控制门禁

`巴法云` 上订阅频道的默认名称为 `门禁`、`电梯`、`上行`、`下行`，类型为开关，所以对 `小爱同学` 说 `打开门禁` 就可以打开门禁了。

同理，也可以说`打开电梯`、`打开上行`、`打开下行`实现对电梯的控制。

### 3. 使用米家App控制门禁

由于米家无法显示和直接控制第三方平台的设备，所以还是需要借助`小爱音响`，在`米家`App中选择 **添加(右上角) -> 手动控制**，可以自定一个控制名称，比如`打开门禁`。然后`添加执行动作`，选择 **家居设备 -> "小爱音响" -> 执行文本命令**，输入`打开门禁`，勾选`静默执行`，点击`完成`。

完成后，首页就会出现一个名为`打开门禁`的快捷按钮，点击就可以打开门禁了。同理，也可以添加`打开电梯`、`打开上行`、`打开下行`的快捷方式，实现电梯的控制。

---

## 六、其他FAQ

### 1. 如何实现内网穿透？

您可以借助一些免费frp穿透服务。如果是个人搭建，除了**frp**，也可以使用**zerotier**或**wiregurad**来实现内网穿透。个人搭建时最好购买域名，并使用https和非80/443端口来访问HA，更安全些，这里不展开讲。

### 2. 如何支持HomeKit？

通过HA的 **HomeKit Bridge** 桥接设备，并通过iOS **家庭** App扫码添加。如果有外网访问需求，请自行额外购买Apple音响或者Apple TV作为中枢。

### 3. 如何支持米家？

方案2已详细描述接入方案，如果您使用的方案1，则需要通过bamfa集成将本地实体接入到米家，并参考方案2支持米家。

### 4. HA配置提示端口被占用？

可修改端口，同时调整室内机和路由器的端口转发规则。

### 5. 消息推送手机后需要等很久才能显示实时画面

目前是配合rtsp流来实现视频推送没有预加载所以慢。不建议开启 **预加载视频流** 来加快推流，这会影响HA性能和其他用户的体验。

### 6.自动挂断功能

目前尚未实现，可能后续会支持。

### 7.室内机是否还有其他功能可以挖掘

有。最简单的就是替换一些资源文件，比如替换桌面壁纸、图标，抑或是替换响铃声音，但注意不要做危险操作，以免损坏系统。

---
