# 浏览器埋点事件知识库

## 基本信息

- **appid**: 31000000442
- **created_at**: 2026-05-09 16:22:07
- **db_version**: 2.0
- **hive_table**: dw.dwd_ot_event_di_31000000442
- **onetrack_dashboard**: https://onetrack.bi.mi.com/#/dashboard?projectId=536
- **product**: 小米浏览器
- **shujing_url**: https://s.mi.cn/HCA7W9
- **source_file**: 浏览器新版OneTrack埋点汇总（可用于神策、数鲸）.xlsx

## 数据概览

| 项目 | 数量 |
|------|------|
| categories | 20 |
| sdk_fields | 32 |
| common_field_groups | 2 |
| common_fields | 71 |
| pages | 87 |
| events | 239 |
| event_fields | 831 |
| event_common_field_refs | 279 |
| event_page_refs | 355 |
| event_metric_refs | 26 |

### 事件分类统计

| 分类 | 中文名 | 事件数 | 说明 |
|------|--------|--------|------|
| ad | 商业化事件 | 49 | 广告商业化事件 |
| content | 信息流事件 | 42 | 信息流内容相关事件（曝光/点击/浏览/播放/互动） |
| ai_search | AI搜索事件 | 37 | AI搜索模块事件 |
| general | 常规事件 | 29 | 多窗口/无痕/阅读模式等常规操作事件 |
| search | 搜索事件 | 18 | 搜索相关事件 |
| app | 浏览器全局事件 | 12 | App级别全局事件（打开/退出/弹窗/引导/升级等） |
| hot | 热榜事件 | 10 | 热榜模块事件 |
| engineering | 工程埋点 | 6 | 研发测试/工程类埋点 |
| personal | 个人中心事件 | 6 | 个人中心页面事件 |
| setting | 设置事件 | 6 | 设置页面事件 |
| push | Push事件 | 5 | 浏览器Push推送事件 |
| ai_browser | AI浏览器事件 | 4 | AI浏览器功能事件 |
| icon_slots | 站点事件 | 4 | 名站/宫格/资源位事件 |
| button_bar | 底部工具栏事件 | 3 | 底部工具栏点击/切换事件 |
| novel | 小说事件 | 3 | 小说功能相关事件 |
| download | 下载事件 | 2 | 文件下载相关事件 |
| livestream | 直播事件 | 2 | 直播SDK相关事件 |
| download_intercept | 下载拦截事件 | 1 | 下载拦截相关事件 |
| hot_content | 信息流热榜内容事件 | 0 | 信息流内热榜内容事件 |
| search_security | 安全网址事件 | 0 | 搜索安全网址服务端事件 |

### 实验ID字段

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| eid | 实验id | string | 服务端下发的实验id
有值传值，无值传空
格式：0:1049:0:0:0:0:0:0:0:0:0:0:0:0:199: |
| exp_id | 大数据新版实验id | string | 有值传值，无值传空
格式：110257,114439,110057 |

### 核心指标 ↔ 事件映射

| 指标 | 关联事件 |
|------|----------|
| 信息流有效用户 | content_item_click |
| 浏览器DAU/日活 | app_open, app_open, app_open_actively, app_open_dp, app_open_third, app_open_third_url, app_open_third_webpage_load_completed |
| 浏览器信息流DAU/日活 | content_item_expose, content_item_click, content_item_expose, content_item_expose_enter, content_item_expose_noenter |
| 浏览器信息流人均VV | content_item_video_over |
| 浏览器信息流人均时长 | app_duration, app_duration, content_duration, app_duration |
| 浏览器信息流人均消费时长 | content_duration, videoplayer_duration |
| 浏览器信息流次日留存率 | content_item_expose, content_item_click |
| 浏览器信息流消费DAU/日活 | content_item_click, content_item_click, content_item_click_enter, content_item_click_noenter |

### 页面 ↔ 事件映射（Top 15）

| 页面 | 中文名 | 关联事件数 |
|------|--------|------------|
| feed_info_topnews | 资讯_热点 | 111 |
| feed_info_rec | 资讯_推荐 | 44 |
| feed_video_rec | 视频_推荐 | 42 |
| home | 浏览器主页 | 37 |
| feed_content_detail | 详情页 | 35 |
| search_result | 搜索结果页 | 17 |
| search_sug | 搜索sug页 | 15 |
| search_home | 搜索首页 | 15 |
| setting |  | 8 |
| me | 我的 | 7 |
| gongge | 宫格 | 7 |
| novel |  | 5 |
| bookmark_BookmarkAndHistory |  | 4 |
| window_window | 窗口_窗口 | 4 |
| web_page |  | 2 |

## OneTrack SDK系统属性

| 属性名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ot_privacy_policy | 打点时的隐私策略 | string | 取值范围为custom_open，custom_close，exprience_open，exprience_close |
| ot_browser_type | 浏览器类型 | string | 浏览器类型，根据User-Agent得出 |
| ot_ua | User-Agent | string | http请求的User-Agent |
| plugin_id | 插件ID | string | 如果sdk是插件模式，会带上插件ID |
| sdk_mode | SDK接入模式 | string | 支持App模式（默认，一般业务选择该模式即可），SDK模式（如小米账号SDK接入），插件模式（如米家/快应用插件） |
| ot_first_day | 首天登录 | boolean | 如果用户是在使用的第一天（UTC8时区），这个字段值为true，否则为false，用来近似（用户清除App数据后再次打开 |
| uid_type | 用户Id的类型 | string | 类型为sdk提供的枚举，如XIAOMI、WEIXIN等，具体参考帮助文档 |
| gaid | GMS（Google服务）生成 | string | GMS（Google服务）生成的广告id，仅在海外采集 |
| uid | 用户设置的userId | string | 在调用login接口后，每条事件都会带该字段，直到登出或是清除数据， 如果没有调用login接口没有该字段key，调用该 |
| event | 事件名 | string | 推荐使用小写字母 + "_" 风格命名；保持和埋点管理平台上注册的事件名称一致，只能是字母、数字、下划线，且只能以字母开 |
| ip | IP | string |  |
| channel | 下载渠道 | string | 一般为业务分发的渠道，比如抖音、应用宝等，用以跟踪渠道效果 |
| pkg | 包名 | string | App的包名 |
| app_id | APPID | string | 业务在埋点管理平台上注册分配的appID |
| sid | 用户空间 | string | 0为用户主空间，999为应用双开空间、其它为系统分身空间 |
| region | 地区 | string | 用户设置的国家/地区 |
| net | 网络 | string | 事件发生（打点）的网络 WIFI/5G/4G/3G/2G/ETHERNET/NONE/UNKNOWN，NONE为没有联网 |
| tz | 时区 | string | 用户设备的时区 |
| e_ts | 上报数据时间戳 | number | 事件发生（打点）的时间戳 |
| sdk_ver | sdk版本号 | string | onetrack sdk的版本号 |
| app_ver | APP版本号 | string | App的版本号 |
| os_ver | 系统版本号 | string | 系统版本号 |
| build | 版本类型 | string | S：稳定版 D： 开发版 A：体验版 空值为用户自己编的版本 |
| miui | MIUI版本号 | string | 系统 ro.build.version.incremental 属性 |
| platform | 平台 | string | Android / iOS /JS / JAVA / GO/watch等 |
| model | 设备名 | string | 设备型号 |
| mfrs | 厂商 | string | 设备产商 |
| android_id | 安卓id | string | 当 imei 为空时，会采集该字段，如果imei有值，则不采集无该字段，刷机/恢复出厂设置会变，系统升级到8.0，用户A |
| oaid | OAID | string | 老的MIUI系统版本没有OAID，用户也可以关闭OAID，OAID是信通院的标准，在MIUI V10.2稳定版后支持，目 |
| instance_id | 匿名ID | string | 匿名ID, SDK自己生成并存在客户端本地，如果是在MIUI上，会保持在系统analytics服务中，APP卸载重装后改 |
| imei | imeiMD5值 | string | 国际版不采集该字段，如果App没有读取imei的权限那么该值为“”，采集imei1字段（imei中较小的那个） |
| cpu_board | cpu型号 | string | 系统自采集cpu平台型号 |

## 公共字段组

### common_key (公共属性)
- 说明: 业务定义的公共属性，每个事件都携带
- 作用域: all

| 字段名 | 中文名 | 类型 | 说明 | 值说明 | 版本 |
|--------|--------|------|------|--------|------|
| imei2 | imei2MD5值 | string |  | imei2的32位md5，有值传值 |  |
| eid | 实验id | string |  | 服务端下发的实验id
有值传值，无值传空
格式：0:1049:0:0:0:0:0:0:0:0:0:0:0:0:199: |  |
| exp_id | 大数据新版实验id | string |  | 有值传值，无值传空
格式：110257,114439,110057 |  |
| homepage_type | 主页类型 | string |  | concise：简洁版
default：默认
custom：自定义 |  |
| deviceid | 设备id | string | 严格按O2O逻辑打，保证同一个用户，在OneTrack的deviceid和O2O的一致。
目的：CP |  | 15.4 |
| app_launch_way | 启动浏览器方式 | string | 热启时也有打，延续最近一次冷起的启动方式；
锁屏再打开记录的是最近一次冷启的启动方式；
15.6版本 | 点击icon
点击push
点击桌面书签
新全搜调起
第三方调起
tool_widget_one(小部件1)
tool_ | 14.3开始有值；
15.6更新取值 |
| today_first_app_launch_way | 用户当天首次启动浏览器方式 | string | 用户当天首次启动方式(按时间区分，首次方式当天值不变) | 点击icon
点击push
点击桌面书签
新全搜调起
第三方调起
tool_widget_one(小部件1)
tool_ | 17.1 |
| third_packagename | 第三方调起包名 | string |  | app_launch_way等于“第三方调起”时，上报第三方调起包名，其余情况为空 |  |
| page | 当前所属页面 | string |  | 见“附1：页面定义” |  |
| from_page | 上级页面 | string |  | 见“附1：页面定义” |  |
| searchengine_name | 搜索引擎名 | string |  | baidu
sogou
sm
toutiao
自定义搜索引擎的名称 |  |
| log_miaccount | 小米账号登录状态（系统、非浏览器） | boolean |  | true ：登录
false：未登录 |  |
| browser_log_status | 浏览器账号登录状态 | boolean |  | true ：登录
false：未登录 |  |
| sreen_resolution | 手机屏幕分辨率 | string |  | 如：640x480 |  |
| desktop_expid | 桌面框实验信息 | string | 实时读取，桌面框本地实验分组（桌面无法联网），故单独使用一个实验字段 | 以点分隔多个实验，如exp-1.exp-2 |  |
| ad_rec_status | 个性化广告推荐开关状态 | string |  | on：打开
off：关闭 | 15.2 |
| content_rec_status | 个性化内容推荐开关状态 | string |  | on：打开
off：关闭 | 15.2 |
| start_source | 桌面框调起标记 | string | 上报逻辑：桌面框调起浏览器时上报此参数（且有值），所有的事件都要带上，一直到离开app。
离开
离开 | 桌面框调起浏览器时上报（包括热启冷起），该字段值为bw-desktop，其他情况为记为空
（目前在实验阶段） | 在15.4删除 |
| baidu_applets | 小程序开关 | boolean |  | true/false |  |
| is_admarket_channel | 是否外投渠道调起 | boolean |  | true/false |  |
| version_name | 小说_浏览器版本 | string |  |  |  |
| novel_MIUIVersion | 小说_MIUI版本 | string |  |  |  |
| index_type | 首页类型 | string |  |  |  |
| icon_switch_status | 宫格开关状态 | string |  |  |  |
| hot_list_switch_status | 热榜开关状态 | string |  |  |  |
| is_admarket_channel | 是否外投渠道调起 | boolean |  |  |  |
| admarket_channel_name | 外投渠道名称 | string |  |  |  |
| session | 进程id | string |  |  |  |
| launchedAppChannel | 外投渠道名名称 | string |  |  |  |
| sessionId | session | string |  |  |  |
| search_logo_type | 搜索图标类型 | string |  |  |  |
| search_button_status | 搜索按钮状态 | string |  |  |  |
| cpu_board | 处理器型号 | string |  | 系统自采集 |  |
| screen_rotation | 屏幕旋转 | string |  | 用户是否设置屏幕旋转 |  |
| dp_ext | dp拓展字段 | string |  |  |  |
| splash_ad_sdk_request_status | 是否成功请求sdk开屏 | boolean |  |  |  |
| app_ver_server | 客户端请求服务端版本号 | string | 版本号为app_version_name | 17.5.90320 |  |
| cp_id | 合作方id | string |  | 头条为头条uuid |  |
| is_coldstart | 是否冷启动 | boolean |  | true：冷启
false：热启 |  |
| model_type | 设备机型类别 | string |  | 手机、折叠屏、pad |  |

## 页面定义

| 页面key | 中文名 | 分类 | 模块key | 模块中文名 | 备注 |
|---------|--------|------|---------|------------|------|
| home | 浏览器主页 | 浏览器主页 - 主页tab |  |  |  |
| gongge | 宫格 | 浏览器主页 - 宫格（浏览器首页左滑进入） |  |  |  |
| search_home | 搜索首页 | 搜索 -  搜索首页 |  |  |  |
| search_sug | 搜索sug页 | 搜索 -  搜索sug页 |  |  |  |
| search_result | 搜索结果页 | 搜索 -  搜索结果页 |  |  |  |
| feed_info_topnews | 资讯_热点 | 信息流进入态 - 资讯tab
（也是信息流列表页） | feed | 推荐流模块 | 热点频道改版，自17.0版本后对应推荐页面 |
| feed_info_rec | 资讯_推荐 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  | 热点频道改版，自17.0版本对应要闻页面 |
| feed_info_videos | 资讯_视频 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_freenovels | 资讯_免费小说 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_shortVideo | 资讯_小视频 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_lianghui | 资讯_两会 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_pneu | 资讯_抗疫 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_game | 资讯_游戏 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_location | 资讯_本地 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_sport | 资讯_体育 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_science | 资讯_科技 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_military | 资讯_军事 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_entertainment | 资讯_娱乐 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_emotion | 资讯_情感 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_finance | 资讯_财经 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_car | 资讯_汽车 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_education | 资讯_教育 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_society | 资讯_社会 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_international | 资讯_国际 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_culture | 资讯_文化 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_history | 资讯_历史 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_household | 资讯_家居 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_tourism | 资讯_旅行 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_food | 资讯_美食 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_fashion | 资讯_时尚 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_parenting | 资讯_育儿 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_health | 资讯_健康 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_constellations | 资讯_星座 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_info_newera | 资讯_新时代 | 信息流进入态 - 资讯tab
（也是信息流列表页） |  |  |  |
| feed_video_rec | 视频_推荐 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_shortv | 视频_小视频 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_game | 视频_游戏 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_jokes | 视频_搞笑 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_film | 视频_影视 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_food | 视频_美食 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_variety | 视频_综艺 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_video_military | 视频_军事 | 信息流进入态 - 视频tab
（也是信息流列表页） |  |  |  |
| feed_content_detail | 详情页 | 信息流进入态 - 详情页 | content | 内容详情模块 |  |
| feed_content_detail_shortvideo | 短视频详情页 | 信息流进入态 - 短视频详情页 |  |  |  |
| feed_minivideo_continuously_root | 小视频内流root页（列表页进入小视频的第一个条内容） | 信息流进入态 - 小视频内流root页 |  |  |  |
| feed_minivideo_continuously | 小视频内流（列表页进入小视频之后，第二条及以后的内容） | 信息流进入态 - 小视频内流页 |  |  |  |
| feed_shortvideo_immerse_root | 短视频沉浸式root页（列表页进入沉浸式后，第一个内容） | 信息流进入态 -  短视频沉浸式root页面 |  |  |  |
| feed_shortvideo_immerse | 短视频沉浸式页面（列表页进入沉浸式后，第二个及以后的内容） | 信息流进入态 -  短视频沉浸页 |  |  |  |
| feed_livestream_immersion | 直播内流页面（沉浸式点击进入直播内流） | 信息流进入态 -  直播内流页 |  |  |  |
| feed_minivideo_continuously |  | 信息流进入态-视频底tab（15.4之后）-小视频 |  |  |  |
| feed_shortvideo_immerse |  | 信息流进入态-视频底tab（15.4之后）-短视频 |  |  |  |
| window_window | 窗口_窗口 | 窗口tab |  |  |  |
| windou_traceless | 窗口_无痕 | 窗口tab |  |  |  |
| me | 我的 | 我的tab |  |  |  |
| setting |  | 设置 |  |  |  |
| launch_splash |  | 过渡页面 |  |  |  |
| bookmark_search |  | 书签搜索 |  |  |  |
| readmode |  | 阅读模式 |  |  |  |
| bookmark_Preview |  | 书签导入 |  |  |  |
| bookmark_content |  | 书签历史页面 文件夹 |  |  |  |
| feed_info_sport_ChannelDetail |  | 体育频道二级页面 |  |  |  |
| feed_info_game_HotChannel |  | 游戏-热门游戏页面 |  |  |  |
| feed_info_location_ChooseCity |  | 城市选择 |  |  |  |
| feed_content_detail_web |  | 信息流详情web实现 |  |  |  |
| atlas |  | 看图模式 |  |  |  |
| wallpaper_CustomWallpaper |  | 自定义壁纸 |  |  |  |
| gallery |  | 画廊 |  |  |  |
| quicklink_QuickLinksAdd |  | 简版书签与历史 |  |  |  |
| bookmark_BookmarkAndHistory |  | 书签与历史 |  |  |  |
| bookmark_VideoHistory |  | 视频历史 |  |  |  |
| search |  | 自定义搜素引擎 |  |  |  |
| feedback |  | 反馈 |  |  |  |
| offlinevideo |  | 我的视频 |  |  |  |
| qrcode |  | 扫一扫 |  |  |  |
| FilePicker |  | 文件选择 |  |  |  |
| mibrowser_dispatcher |  | 浏览器分发(技术实现) |  |  |  |
| guide |  | 引导 |  |  |  |
| guide_guideagreement |  | 用户协议 |  |  |  |
| novel |  | 小说 |  |  |  |
| feed_content_comments_detail |  | 文章评论详情 |  |  |  |
| usertask |  | 用户任务 |  |  |  |
| netdiagno_DiagnosticDetail |  | 诊断详情 |  |  |  |
| netdiagno_NetWorkDiagnostic |  | 网络诊断 |  |  |  |
| netdiagno_NetworkDiagnosticsTip |  | 网络诊断提示 |  |  |  |
| permission_WebPermissionDetail |  | 权限拦截内容 |  |  |  |
| permission_WebPermissionGuid |  | 权限拦截引导 |  |  |  |
| web_page |  | 网页 |  |  |  |

## 事件详情（按分类）

### app - 浏览器全局事件
*App级别全局事件（打开/退出/弹窗/引导/升级等）*

#### app_open (打开app)
- **上报时机**: APP启动到前台时上报（新用户：cta认证通过后曝光了主页面后上报；老用户：app启动到前台即上报）
进入到前台包括：
点击桌面icon进入、从其他app返回、其他app调起、拉回通知栏、从多任务进入、屏幕解锁、push、点击桌面书签进入
- **无痕模式上报**: 是
- **版本**: 14.3
- **公共属性引用**: common_key(公共属性)
- **关联页面**: home(浏览器主页), gongge(宫格)
- **关联指标**: 浏览器DAU/日活, 浏览器DAU/日活

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| homepage_customized_url | 自定义主页url | string | 记录全值（完整url） | 主页类型为"自定义"时上报 |
| $is_first_day | 是否首日访问 | boolean | true（参数值固定为true） | 在神策上区分用户首日/首次访问 |
| $is_first_time | 是否首次触发事件 | boolean | true（参数值固定为true） |  |
| is_parental_guard | 是否处于家长守护模式 | boolean | true:家长守护
false:不是家长守护 |  |
| guard_type | 家长守护类型 | string | 默认：default
白名单：whitelist
黑名单：blacklist | 默认：家长未设置黑/白名单
白名单：家长设置了「仅允许访问」
黑名单：家长设置了「禁止访问」 |
| third_packagename | 第三方调起包名 | string | app_launch_way等于“第三方调起”时，上报第三方调起包名，其余情况为空 |  |
| is_receive_notification | 通知开关状态 | string | on：开
off：关 | 依赖于浏览器内设置中“接收消息通知”按钮的状态 |
| notification_bar_status | 系统的通知栏通知开关状态 | string | on：开
off：关 | 依赖于系统消息通知栏通知开关的状态 |
| splash_ad_request_status | 是否请求开屏广告 | boolean | true:：是
false ：否 |  |
| default_browser | 系统默认浏览器 | string | 上报当前的默认浏览器包名 |  |
| web_security | 是否开启安全网址检测开关 | string | true:：是
false ：否 |  |
| incognito_status | 无痕模式的状态 | string | true:：无痕模式
false ：普通模式 |  |
| is_kid_account | 是否登陆未成年账号 | boolean | true:：是
false ：否 |  |
| is_direct_search | 是否默认【直达】为首页 | boolean | true：是
false：否 |  |
| is_order_search | 是否命中强切 | boolean | true：是
false：否 |  |

#### app_duration (app停留时长)
- **上报时机**: APP退出(包含退出到后台)时上报
上报从前台到退出的时长
退出到后台包括：回到桌面、返回到其他app、调起其他app、拉出通知栏、切到多任务、息屏、锁屏
- **无痕模式上报**: 是
- **版本**: 14.3
- **公共属性引用**: common_key(公共属性)
- **关联页面**: home(浏览器主页), feed_info_topnews(资讯_热点), feed_content_detail(详情页)
- **关联指标**: 浏览器信息流人均时长, 浏览器信息流人均时长, 浏览器信息流人均时长

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| duration_type | 时长类型 | string | app_total |  |
| duration | 时长 | number | 单位：毫秒
查询时需限定：
时长>0&时长<86400000(单位毫秒)
以排除异常值 |  |
| homepage_customized_url | 自定义主页url | string | 记录全值（完整url） | 主页类型为"自定义"时上报 |
| third_packagename | 第三方调起包名 | string | app_launch_way等于“第三方调起”时，上报第三方调起包名，其余情况为空 |  |

#### webpage_performance (网页_性能)
- **上报时机**: 网页加载完成之后，内核计算出指标结果后，通知客户端，客户端上传到one track
- **公共属性引用**: common_key(公共属性)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| dns | dns解析 | number | 单位：毫秒 |  |
| connect | 网络连接 | number | 单位：毫秒 |  |
| fpt | 读取页面第一个字节数的时间 | number | 单位：毫秒 |  |
| load | 页面加载时间 | number | 单位：毫秒 | 开始加载到加载结束的耗时 |
| ttfb | 首包时间 | number | 单位：毫秒 |  |
| http | 数据传输耗时 | number | 单位：毫秒 |  |
| fp | 首次绘制 | number | 单位：毫秒 |  |
| fcp | 首次内容绘制 | number | 单位：毫秒 |  |
| lcp | 最大内容绘制 | number | 单位：毫秒 |  |
| fid | 首次输入延迟 | number | 单位：毫秒 |  |
| cls | 累计位移偏移 | number | 单位：毫秒 |  |
| shut_down | 用户手动取消加载 | number | 单位：毫秒 |  |
| host | 网站域名(实验包参数) | string |  |  |
| isVpn | 是否开启vpn(实验包参数) | boolean |  |  |

#### open_external_app (open_external_app)
- **上报时机**: 浏览器调起第三方app时上报
- **备注**: 浏览器deeplink场景增加打点需求

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| common key 公共属性 |  |  |  | 浏览器deeplink场景增加打点需求 |
| open_external_source 调起三方app来源 | string | from_ad：广告 from_web：第三方网页（含百度搜索结果页） |  |  |
| deeplink_schema | string | 完整的schema字段 |  |  |
| domain_name | string | 域名 |  |  |
| open_external_packagename | string | app包名 |  |  |
| open_external_name | string | app名称 |  |  |

#### baidu_applet_change_permission (百度小程序权限变更)
- **上报时机**: 上报场景1. 用户首次触发小程序授权弹窗，并授权时
上报场景2. 用户进行权限调整时
- **备注**: 预置属性已包含distinct_id，不需要额外上报
权限修改时间，使用e_ts
- **版本**: 【PRD】百度小程序-用户权限深度合作项目（内部）
- **公共属性引用**: common_key(公共属性)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| applet_id | 小程序id | string |  |  |
| applet_name | 小程序名称 | string |  |  |
| permission_type | 权限类型 | string | position：获取你的地理位置信息
photo：访问手机相册
camera：使用你的手机摄像头
microphone：使用你的麦克风
addresslist |  |
| permission_status | 权限使用状态 | string | 用户操作后的状态
allow：允许
refuse：拒绝
unused：未使用 |  |

#### search_scan_click_browser (浏览器原生搜索框扫一扫点击)
- **上报时机**: 包括场景：首页
- **版本**: 【V16.8】浏览器&全搜扫一扫
- **公共属性引用**: common_key(公共属性)
- **关联页面**: search_home(搜索首页), search_sug(搜索sug页), search_result(搜索结果页)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| card_type | 模块类型 | string | 扫一扫 |  |
| fromWidget | 来源 | string | true：桌面小部件
false：全搜打开 |  |

#### search_scan_imp_browser (浏览器原生搜索框扫一扫页面曝光)
- **上报时机**: 扫描页面曝光时上报
- **版本**: 【V16.8】浏览器&全搜扫一扫
- **公共属性引用**: common_key(公共属性)
- **关联页面**: search_home(搜索首页), search_sug(搜索sug页), search_result(搜索结果页)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| fromWidget | 来源 | string | true：桌面小部件
false：全搜打开 |  |

#### translation_error_code (翻译错误代码)
- **上报时机**: 当翻译失败的时候上报错误代码参数
- **公共属性引用**: common_key(公共属性)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| code | 错误代码 | number | 1 : 翻译脚本未设置；
2 : 脚本注入失败;
6 : 翻译失败；
7 : 翻译脚本初始化失败,超时
12 : 后续页面翻译错误 | 研发用打点，用于记录翻译错误的代码，以便之后用于排查翻译错误问题 |

#### page_translate_click (划词翻译)
- **公共属性引用**: common_key(公共属性)

#### translation_window_click (翻译弹窗点击)
- **公共属性引用**: common_key(公共属性)

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| function | 功能名称 | string |  |  |
| url | 网页域名 | string |  |  |

#### translation_window_expose (翻译弹窗曝光)
- **公共属性引用**: common_key(公共属性)

#### app_open_third_webpage_load_completed (三方调起浏览器网页加载完成)
- **上报时机**: 三方调起浏览器网页加载完成时上报
- **备注**: 考虑到url上报存储很大，采样率设置为50%
- **关联指标**: 浏览器DAU/日活

| 字段名 | 中文名 | 类型 | 值说明 | 备注 |
|--------|--------|------|--------|------|
| third_packagename | 第三方调起包名 | string |  | 考虑到url上报存储很大，采样率设置为50% |
| third_url | 第三方调起网页url | string |  |  |
| load_status | 加载状态 | string | 加载成功：load_success
加载失败：load_failed
加载超时：load_timeout |  |

## 常用查询示例

```sql
-- 1. 按指标查关联事件
SELECT e.name, e.name_cn FROM events e
JOIN event_metric_refs m ON e.id=m.event_id
WHERE m.metric_name='浏览器信息流人均时长';

-- 2. 按页面查关联事件
SELECT e.name, e.name_cn FROM events e
JOIN event_page_refs r ON e.id=r.event_id
JOIN pages p ON r.page_id=p.id
WHERE p.page_key='feed_info_topnews';

-- 3. 按分类查所有事件
SELECT name, name_cn FROM events WHERE category='content';

-- 4. 查事件的完整信息（字段+公共属性+页面+指标）
SELECT * FROM event_fields WHERE event_id=(SELECT id FROM events WHERE name='content_item_expose');
SELECT g.name FROM event_common_field_refs r JOIN common_field_groups g ON r.group_id=g.id WHERE r.event_id=(SELECT id FROM events WHERE name='content_item_expose');
SELECT p.page_key FROM event_page_refs r JOIN pages p ON r.page_id=p.id WHERE r.event_id=(SELECT id FROM events WHERE name='content_item_expose');
SELECT metric_name FROM event_metric_refs WHERE event_id=(SELECT id FROM events WHERE name='content_item_expose');

-- 5. 查实验ID字段
SELECT name, name_cn, type, value_note FROM common_fields WHERE name IN ('eid', 'exp_id');

-- 6. 查页面定义
SELECT page_key, name_cn, category FROM pages WHERE category LIKE '%信息流%';
```
