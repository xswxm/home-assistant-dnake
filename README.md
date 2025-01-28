# 狄耐克门禁系统（Dnake） Home Assistant 集成

通过HA集成接入Dnake后可以实现远程控制门禁开启和电梯、监听室内机呼叫并推送等功能。

<a href="demo"><img src="https://github.com/xswxm/home-assistant-dnake/blob/main/demo.gif?raw=true" width="480" ></a>

**注意：切勿利用本教程破坏互联网安全，影响居民生活。**

---

## 一、配置室内机

### 1. 获取室内机信息

室内机进入 **设置 -> 网络设置**（默认密码为`123456`），获取IP地址、子网掩码、默认网关和服务器相关信息。

室内机进入 **设置 -> 房号设置** 获取栋号、单元和房号。

---

## 二、配置网络

### 1. 连接交换机

由于室内机与服务器和室外机在同一个网络，可以在室内机前增加一台交换机，并将原有连接室内机的网线、室内机、和OpenWRT路由器连接至同一个交换机。

### 2. 配置OpenWRT

- 进入 **OpenWRT -> 网络 -> 接口 -> 添加端口**，增加端口配置：
  
  - 端口：选择你实际使用的物理网口，如 **eth1**
  - 协议：**静态IP**
  - IPv4地址：参考之前室内机的IP和网段，填入一个不会引起冲突的IP地址
  - IPv4子网掩码：参考室内机填写
  - IPv4网关：参考室内机填写
  - IPv4广播：留空
  - DNS服务器：参考室内机填写
  - 其他注意实现：不要启用DHCP和IPv6相关功能，注意配置防火墙
- 进入 **OpenWRT -> 网络 -> 静态路由**，增加静态路由配置：
  
  - 接口：**lan**
  - 对象：填Dnake网络的网段，如 **172.16.0.0**
  - IPv4子网掩码：填室内机的 **子网掩码**
  - IPv4网关：填你设置的 **并网IP**
  - 跃迁点：比默认0大即可
- 成功配置后，路由器下设备可以`ping`通室内机。

### 3. 配置端口转发

参考以下配置两个端口（具体端口视实际情况而定）：

- **Dnake消息服务器端口**：映射到局域网中的HA主机（例如`30884`映射到`192.168.123.10`）。
- **内网HTTP Server端口**：映射到内网PC主机（例如`8080`）。

---

## 三、安装室内机客户端

### 1. 启用PC端HTTP Server

在PC端安装Python环境后运行以下命令启动HTTP服务：

```bash
python -m http.server 8080
```

### 2. Telnet连接室内机

- 打开终端（如CMD），通过Telnet连接室内机（注意将 **172.16.1.111** 替换成你的室内机IP）：

```bash
telnet 172.16.1.111 9900
```

- 如果提示Telnet不可用，请在 **控制面板 -> 程序 -> 启用或关闭Windows功能** 中启用Telnet功能。

### 3. 安装呼叫监听客户端

telnet连接室内机后，逐条运行以下命令（注意将 **172.16.1.233** 替换成你的室内机IP）：

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

- 编辑完成后运行以下命令检查程序是否可以正常运行（注意将 **172.16.1.233** 替换成你的室内机IP）：

```bash
/dnake/data/sip_monitor 172.16.1.233:30884 &
```

如果正常，运行 `reboot` 重启室内机。

---

## 四、安装并配置HA集成

### 1. 安装集成

将集成（`dnake`文件夹）通过FTP或Samba复制到HA的`/config/custom_components`目录，并重启HA。

### 2. 配置集成

进入 **HA -> 设置 -> 添加集成**，搜索`dnake`并开始配置以下信息：

- 栋号、单元、房号、室内机IP地址：填入之前室内机上获取的相关信息。
- 家庭ID：默认为1
- 电梯ID：0为所有电梯，1、2、3对应具体电梯编号
- 呼叫监听端口：默认为30884
- 室外机设备：可不填，格式可参考`{"20007": "172.16.0.252"}`。
- MQTT支持：可配置MQTT服务以增加可玩性。

---

## 五、功能实测

### 1. 常规功能

- **门禁控制**：选择门禁设备后，点击打开门禁。
- **电梯控制**：选择门禁设备后，点击对应电梯操作。
- **相机预览**：显示每个门禁设备的预览图像。
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
  - data: {}
    action: script.dnake
    enabled: false
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

## 六、其他FAQ

### 1. 如何实现内网穿透？

你可以借助一些免费frp穿透服务。如果是个人搭建，除了**frp**，也可以使用**zerotier**或**wiregurad**来实现内网穿透。个人搭建时最好购买域名，并使用https和非80/443端口来访问HA，更安全些，这里不展开讲。

### 2. 如何支持HomeKit？

通过HA的 **HomeKit Bridge** 桥接设备，并通过iOS **家庭** App扫码添加。如果有外网访问需求，请自行额外购买Apple音响或者Apple TV作为中枢。

### 3. 如何支持米家？

可以通过bamfa集成将本地实体接入到米家（未实测）。

### 4. HA配置提示端口被占用？

可修改端口，同时调整室内机和路由器的端口转发规则。

### 5. 消息推送手机后需要等很久才能显示实时画面

目前是配合rtsp流来实现视频推送没有预加载所以慢。不建议开启 **预加载视频流** 来加快推流，这会影响HA性能和其他用户的体验。

### 6.自动挂断功能

目前尚未实现，可能后续会支持。

### 7.室内机是否还有其他功能可以挖掘

有。最简单的就是替换一些资源文件，比如替换桌面壁纸、图标，抑或是替换响铃声音，但注意不要做危险操作，以免损坏系统。

---
