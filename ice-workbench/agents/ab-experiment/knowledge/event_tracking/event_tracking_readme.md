# 埋点事件知识库 - 数据摘要

> 数据源: `event_tracking.db` (SQLite) | 生成脚本: `generate_readme.py`

## 总览

| 维度 | 数量 |
|------|------|
| 事件总数 | 122 |
| 事件特有字段 | 879 |
| 公共字段 | 97 |
| 指标关联 | 23 |
| 页面关联 | 193 |

## 事件分类

| 分类 | 数量 | 说明 |
|------|------|------|
| content | 33 | 内容相关（曝光/点击/浏览/播放/互动） |
| app | 24 | app通用（打开/退出/弹窗/引导） |
| search | 15 | 搜索相关 |
| operation | 10 | 运营位 |
| ad | 9 | 广告 |
| livestream | 9 | 直播间 |
| skit | 8 | 短剧 |
| incentive | 6 | 激励体系 |
| exception | 3 | 异常事件 |
| me | 2 | 我的页面 |
| tab | 2 | tab标签 |
| growth | 1 | 拉新拉活 |

## 核心指标 <-> 事件映射

| 核心指标 | 关联事件 |
|----------|---------|
| 信息流有效用户 | content_item_expose, content_count_item |
| 浏览器DAU/日活 | app_open, app_open_v2 |
| 浏览器信息流DAU/日活 | content_item_expose |
| 浏览器信息流人均VV | content_item_video_play, content_item_video_over, content_item_video_auto_play, content_item_video_auto_over |
| 浏览器信息流人均时长 | app_duration_v2, page_duration, content_duration, content_duration_v2 |
| 浏览器信息流人均消费时长 | page_duration, content_item_view, content_item_video_over, content_duration, content_duration_v2 |
| 浏览器信息流次日留存率 | app_open, app_open_v2 |
| 浏览器信息流消费DAU/日活 | content_item_click, content_item_view, content_item_video_play |

## 实验ID字段

| 字段名 | 类型 | 说明 | 位置 |
|--------|------|------|------|
| eid | string | 旧实验id | 公共参数（所有事件携带） |
| new_eid | string | 新实验id（服务端下发） | 公共参数（所有事件携带） |
| ad_exp_id | string | 广告实验id | 广告事件特有字段 |

## 事件详情（按分类）

### ad (广告)

#### `ad_request` — 广告请求

**上报时机**: 事件发生时  单次请求x个广告上报x次

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| item_root_id | 沉浸态首个文章id | string | 沉浸式及小视频内流从第二个播放内容开始之后每个内容（包括广告）都需要记录此值，值为第一个内容的id |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| is_insert_middle_ad | 是否中插广告 | boolean | true：中插广告 false |

**关联页面**: 首页/推荐页, 首页, 沉浸式详情页

**引用公共字段组**: 公共参数

#### `ad_return` — 广告返回

**上报时机**: 广告返回：服务端接收广告返回时即上报 广告曝光：曝光沿用目前o2o广告曝光逻辑，曝光15秒后，再滑会，重复上报 广告点击：点击即上报；多次点击多次上报 广告负反馈：一级弹窗点击条目标签内容上报 视频广告播放完成：广告播放完成、离开广告播放页面时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 竖版视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |
| ad_feedback_type | 反馈类型 | string | 不感兴趣/出现过于频繁/内容质量差 |
| ad_click_area | 点击区域 | string | 广告区/按钮/标签区/左滑/滑动区 |
| ad_click_button_type | 点击按钮类型 | string | 应用下载/查看详情/立即跳转...... |
| request_status | 请求状态 | bool | true/false |
| request_error_info |  | string | 请求成功报null，失败报错误码【仅穿山甲】 |
| app_status | app安装状态 | string | installed/notInstalled |
| ad_img_count | 图片数量 | int | 0，1，2，3，4 |
| ad_return_type | 广告填充类型 | string | normal/flexible/add/back/screen_off |
| ad_position | 广告曝光的位置 | int | 1，2，3，4.... |
| page_number | 页码 | int | 0，1，2，3，4.... |
| ad_req_id | 广告请求id | string |  |
| positionId（新增） | 广告下发位置 | int | 1，2，3，4.... |
| Pagenum（新增） | 广告刷次 | int | 0，1，2，3，4.... |
| is_insert_middle_ad | 是否中插广告 | boolean | true：中插广告 false |
| duration | 时长 | number | 单位毫秒 |
| item_video_length | 广告长度 | number | 单位毫秒 |
| item_percent | 广告播放进度 | number | 播放完成后记录percent，百分比例如  0/1/50/100，保留整数； |
| item_root_id | 沉浸态首个文章id | string | 沉浸式及小视频内流从第二个播放内容开始之后每个内容（包括广告）都需要记录此值，值为第一个内容的id |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| is_high_value | 是否高价值（激励广告） | boolean | true false |

**引用公共字段组**: 公共参数

#### `ad_negative` — 广告负反馈

**上报时机**: 广告返回：服务端接收广告返回时即上报 广告曝光：曝光沿用目前o2o广告曝光逻辑，曝光15秒后，再滑会，重复上报 广告点击：点击即上报；多次点击多次上报 广告负反馈：一级弹窗点击条目标签内容上报 视频广告播放完成：广告播放完成、离开广告播放页面时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 竖版视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |
| ad_feedback_type | 反馈类型 | string | 不感兴趣/出现过于频繁/内容质量差 |
| ad_click_area | 点击区域 | string | 广告区/按钮/标签区/左滑/滑动区 |
| ad_click_button_type | 点击按钮类型 | string | 应用下载/查看详情/立即跳转...... |
| request_status | 请求状态 | bool | true/false |
| request_error_info |  | string | 请求成功报null，失败报错误码【仅穿山甲】 |
| app_status | app安装状态 | string | installed/notInstalled |
| ad_img_count | 图片数量 | int | 0，1，2，3，4 |
| ad_return_type | 广告填充类型 | string | normal/flexible/add/back/screen_off |
| ad_position | 广告曝光的位置 | int | 1，2，3，4.... |
| page_number | 页码 | int | 0，1，2，3，4.... |
| ad_req_id | 广告请求id | string |  |
| positionId（新增） | 广告下发位置 | int | 1，2，3，4.... |
| Pagenum（新增） | 广告刷次 | int | 0，1，2，3，4.... |
| is_insert_middle_ad | 是否中插广告 | boolean | true：中插广告 false |
| duration | 时长 | number | 单位毫秒 |
| item_video_length | 广告长度 | number | 单位毫秒 |
| item_percent | 广告播放进度 | number | 播放完成后记录percent，百分比例如  0/1/50/100，保留整数； |
| item_root_id | 沉浸态首个文章id | string | 沉浸式及小视频内流从第二个播放内容开始之后每个内容（包括广告）都需要记录此值，值为第一个内容的id |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| is_high_value | 是否高价值（激励广告） | boolean | true false |

**引用公共字段组**: 公共参数

#### `ad_landing_page_expose` — 广告落地页曝光

**上报时机**: 广告落地页曝光：进入落地页后计曝光，二次/多次点击进入/重新加载点击进入计多次曝光（不考虑息屏后亮屏/三方切回） 加载按钮点击：点击即上报；多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| landing_status | 加载状态 | bool | true/false |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |

**引用公共字段组**: 公共参数

#### `ad_landing_button_click` — 加载按钮点击

**上报时机**: 广告落地页曝光：进入落地页后计曝光，二次/多次点击进入/重新加载点击进入计多次曝光（不考虑息屏后亮屏/三方切回） 加载按钮点击：点击即上报；多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| landing_status | 加载状态 | bool | true/false |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |

**引用公共字段组**: 公共参数

#### `ad_deeplink_start` — 广告开始调起deeplink

**上报时机**: 4.8版本新增。

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| ad_deeplink_type | 链接类型 | string | deeplink/packagename |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |

**引用公共字段组**: 公共参数

#### `ad_deeplink_result` — 广告deeplink调起结果

**上报时机**: 4.8版本新增

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| ad_deeplink_type | 链接类型 | string | deeplink/packagename |
| is_success | 是否成功 | bool | true/false |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |

**引用公共字段组**: 公共参数

#### `ad_wechat_mini` — 广告拉起微信小程序

**上报时机**: 读取小程序原始id，内容中心广告准备拉起微信小程序时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| to_mini | 拉起小程序 | boolean | true: 广告拉起小程序成功 false: 广告拉起小程序失败 |
| h5_url | 页面url | boolean | true: url不为空，拉起h5页面成功 false: url为空，拉起h5页面失败 |

**引用公共字段组**: 公共参数

#### `ad_anti_cheat` — 广告反作弊事件

**上报时机**: 反作弊出现时机时上报：进入广告落地页发起拦截时上报。

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ad_anti_type | 反作弊类型 | string | 唤端成功拦截 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |

**引用公共字段组**: 公共参数

### app (app通用（打开/退出/弹窗/引导）)

#### `app_open` — app打开

**上报时机**: 内容中心打开进入前台就上报 进入前台定义：桌面上滑，push调启，负一屏调启，多任务切回，从息屏锁屏到亮屏

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| open_type | 上滑：launch_swipe
push：push
负一屏：assistant
锁屏息屏：lock_screen
小部件: widget_4*2hot，widget_4*2recommend，widget_4*4hot
快捷方式：shortcut
拉活进入：DP中的source
全搜为你推荐icon：quick_search | 4*4 热点资讯：widget_4*4hot
4*2 热点资讯：widget_4*2recommend
4*2 实时热榜：widget_4*2hot |  |

**关联指标**: 浏览器DAU/日活, 浏览器信息流次日留存率
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_duration（废弃）` — app退出

**上报时机**: 内容中心退出时上报时长 用户从前台切到后台，上报从前台-后台的时长 切到后台定义：app退出桌面，锁屏/息屏/多任务切第三方/通知栏跳三方

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | 停留时长 | string |  |

**引用公共字段组**: 公共参数

#### `app_cta_click` — CTA点击激活

**上报时机**: 事件发生时

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| expose_cnt | 曝光次数 | string |  |
| popup_style | 弹窗样式 | 1，2，3 |  |
| from_type | cta激活前之前的模式 | normal mode, only_view mode | normal mode - 未进入基础模式，cta页面点击同意的用户 only_view mode - 进入基础模式后，再在cta页面点击同意的用户 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_cta_expose` — cta弹窗曝光

**上报时机**: 事件发生时 曝光几次记几次 比如退出后再进入，从三方返回

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| popup_style | 1,2,3 | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_open_v2` — app打开过程

**上报时机**: app进入前台上报： 前台分流上/详情页 详细规则：前台看见流上上报打开事件，打开参数为流上 前台看见详情页上报打开事件，打开参数为详情页

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| open_type | feed/detail | string |  |

**关联指标**: 浏览器DAU/日活, 浏览器信息流次日留存率
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_duration_v2` — app退出过程

**上报时机**: app退出前台上报： 退出流上/详情页 详细规则：从前台看见流上，开始计时，看不到流上报流上时长。 从前台看见详情页，开始计时，看不到详情页报详情页时长。

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | 停留时长 | string |  |
| duration_type | feed/detail/
livestream | string |  |

**关联指标**: 浏览器信息流人均时长
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_popup_window_expose` — app弹窗曝光

**上报时机**: 弹窗曝光即上报，弹出几次，上报几次。不去重 page、from_page、module、from_module为空

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| popup_type | swich_entertainment //邀请您体验娱乐中心
swich_weibo_main_app //主频道微博弹窗跳微博
swich_weibo_main_fast //主频道微博弹窗跳快应用
swich_weibo_hot_app //热榜频道微博弹窗跳微博
swich_weibo_hot_fast //热榜频道微博弹窗跳快应用
privacy_update//隐私弹窗更新
privacy_deny//隐私弹窗撤回
accept_shortcut //快捷方式
active_back//拉活返回弹窗 | string |  |
| exp_id | 实验ID | string |  |
| item_docid | 内容id | string |  |
| popup_style | 1,2,3 | number |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_popup_window_click` — app弹窗点击

**上报时机**: 点击取消，确定按钮即上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| popup_type | swich_entertainment //邀请您体验娱乐中心
swich_weibo_main_app //主频道微博弹窗跳微博
swich_weibo_main_fast //主频道微博弹窗跳快应用
swich_weibo_hot_app //热榜频道微博弹窗跳微博
swich_weibo_hot_fast //热榜频道微博弹窗跳快应用
privacy_update
privacy_deny
accept_shortcut //快捷方式
active_back//拉活返回弹窗 | string |  |
| popup_click_type | cancel/agree | string |  |
| exp_id | 实验ID | string |  |
| item_docid | 内容id | string |  |
| popup_style | 1,2,3 | number |  |
| expose_cnt | 10 | number |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_guide_expose` — 引导曝光

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| guide_type | click：点击引导
slide：滑动引导
active：拉活引导 | string |  |
| guide_name | novel_first-小说新用户引导-首次气泡
novel_red-小说新用户引导-小红点 | string |  |
| guide_style | 续读状态1全屏展示
续读状态2小卡展示 | string | 续读类型 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_guide_click` — 引导点击

**上报时机**: 点击X，去试试按钮即上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| guide_click_type | cancel/agree | string |  |
| guide_name | novel_first-小说新用户引导-首次气泡
novel_red-小说新用户引导-小红点 | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_top_slide` — 置顶滑动

**上报时机**: 滑动成功触发

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| slide_type | 滑动方式 | 页面1左滑至页面2上报left_1
页面2左滑至热榜频道上报left_2
右滑上报right |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `app_top_slide_expose` — “左滑查看全部”按钮曝光

**上报时机**: 刷新（有数据请求）后重复曝光

**引用公共字段组**: 公共参数

#### `app_top_slide_click` — “左滑查看全部”按钮点击

**上报时机**: 点击几次上报几次

**引用公共字段组**: 公共参数

#### `app_hot_more` — “查看完整榜单”按钮点击

**上报时机**: 点击几次上报几次

**引用公共字段组**: 公共参数

#### `notice_bell_click` — 铃铛点击

**上报时机**: 点击触发，点击几次报几次

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `page_duration` — 页面时长

**上报时机**: 进入页面开始计时，离开页面上报页面时长

**关联指标**: 浏览器信息流人均时长, 浏览器信息流人均消费时长
**关联页面**: 首页/推荐页, 首页, 图文详情页, 沉浸式详情页, 短剧详情页

**引用公共字段组**: 公共参数

#### `button_click` — 按钮点击

**上报时机**: 点击时上报，点击几次上报几次

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| button_type | 按钮类型 | button//全屏按钮
press_2.0//长按2.0X
0.75X//倍速按钮0.75X
1.0X//倍速按钮1.0X
1.25X//倍速按钮1.25X
1.5X//倍速按钮1.5X
2.0X//倍速按钮2.0X
circulate_on：开启循环播放
circulate_off：关闭循环播放 |  |

**关联页面**: 沉浸式详情页, 短剧详情页

**引用公共字段组**: 公共参数

#### `thirdapp_open` — 第三方app拉活

**上报时机**: 进行拉活任务后上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string | 131001 |
| mission_status | 任务状态 | string | 0：拉活成功 1：拉活失败 |
| mission_id | 任务id | string | 131001 |
| mission_status | 任务状态 | string | 0：拉活成功 1：拉活失败 |

**引用公共字段组**: 公共参数, 公共参数

#### `thirdapp_download` — 第三方app拉新

**上报时机**: 进行拉新任务后上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string | 131001 |
| mission_status | 任务状态 | string | 0：拉新成功（点击弹窗就算） 1：安装成功 2：拉启应用成功 3：本地已有该应用 4：本地暂无该应用，且无安装包 5：本地暂无该应用，有安装包，但用户拒绝安装 |
| mission_id | 任务id | string | 131001 |
| mission_status | 任务状态 | string | 0：拉新成功（点击弹窗就算） 1：安装成功 2：拉启应用成功 3：本地已有该应用 4：用户拒绝安装 |

**引用公共字段组**: 公共参数, 公共参数

#### `popup_expose` — 拉新弹窗曝光

**上报时机**: 拉新弹窗露出2/3以上时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string | 131001 |
| mission_id | 任务id | string | 131001 |

**引用公共字段组**: 公共参数, 公共参数

#### `popup_click` — 拉新弹窗点击

**上报时机**: 拉新弹窗点击体验时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string | 131001 |
| mission_id | 任务id | string | 131001 |

**引用公共字段组**: 公共参数, 公共参数

#### `popup_skip` — 拉新弹窗跳过

**上报时机**: 拉新弹窗点击跳过时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string |  |

**引用公共字段组**: 公共参数, 公共参数

#### `page_expose` — 页面曝光

**上报时机**: 点击评论按钮或评论框，弹出评论页面时，上报埋点 重复上报 包括各频道各体裁的评论页面

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| page_name | 页面 | string | 评论页面：comment_detail |

**关联页面**: 图文详情页, 沉浸式详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `launch_swipe_app_open_fail` — 上滑打开失败

**上报时机**: 冷启上滑但未划到顶部未打开内容中心就退出时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| is_new_effect | 新动效是否生效 | boolean |  |
| is_interface_request | 是否有接口请求 | boolean | true/false |

**关联页面**: 首页

### content (内容相关（曝光/点击/浏览/播放/互动）)

#### `content_item_expose` — 信息流_单条内容_曝光

**上报时机**: 信息流_单条内容_曝光：33%条目曝光时上报；不重复上报，需缓存内容（知乎、微博等均上报、沉浸态上报） 信息流_单条内容_点击：事件发生时；多次点击多次上报； 注意： 1、从列表点击进入短小视频沉浸态上报点击 2、上下滑自动播放（包括回看），播放之后自动播放下一个，不上报点击 3、5.6版本点击列表页的内容，进入沉浸态，该条内容不上报content_item_click事件  信息流_单条内容_浏

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| page | 操作所属页面 | string | 轻应用短剧详情页：lightapp_skit_detail 内流短剧详情页：inline_skit_detail |
| from_page | 操作上级页面 | string |  |
| feed_channel | 频道 | string | feed_channel='favourite' |
| item_position | 曝光位置 | number | 短剧沉浸态无此参数 |
| category_name | 频道 | string | 剧集列表没有传category，根据参数本身频道的含义： 通过某X短剧点开的选集面板进入的短剧都跟随该X短剧的category，具体是： 1，通过推荐流插卡点击短剧卡片观看该短剧（category=' |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| chapter_count | 短剧剧集数 | number | 短剧总集数(短剧有几集就报几集) |
| item_cp_name | cp名称 | string | 火山：toutiao-newhome 小米视频：mivideo_newhome |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条/mivideo |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| e_ts | 事件发生时间 | number |  |
| req_id | 请求id | string |  |

**关联指标**: 浏览器信息流DAU/日活, 信息流有效用户
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_click` — 信息流_单条内容_点击

**上报时机**: 信息流_单条内容_曝光：33%条目曝光时上报；不重复上报，需缓存内容（知乎、微博等均上报、沉浸态上报） 信息流_单条内容_点击：事件发生时；多次点击多次上报； 注意： 1、从列表点击进入短小视频沉浸态上报点击 2、上下滑自动播放（包括回看），播放之后自动播放下一个，不上报点击 3、5.6版本点击列表页的内容，进入沉浸态，该条内容不上报content_item_click事件  信息流_单条内容_浏

**关联指标**: 浏览器信息流消费DAU/日活
**关联页面**: 首页/推荐页, 首页, 图文详情页, 沉浸式详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_view` — 信息流_单条内容_浏览

**上报时机**: 信息流_单条内容_曝光：33%条目曝光时上报；不重复上报，需缓存内容（知乎、微博等均上报、沉浸态上报） 信息流_单条内容_点击：事件发生时；多次点击多次上报； 注意： 1、从列表点击进入短小视频沉浸态上报点击 2、上下滑自动播放（包括回看），播放之后自动播放下一个，不上报点击 3、5.6版本点击列表页的内容，进入沉浸态，该条内容不上报content_item_click事件  信息流_单条内容_浏

**关联指标**: 浏览器信息流消费DAU/日活, 浏览器信息流人均消费时长
**关联页面**: 图文详情页, 沉浸式详情页, 短剧详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_video_play` — 信息流_单条内容_视频播放

**上报时机**: 信息流_单条内容_视频播放：视频播放时上报；多次播放多次上报；（退出再进入/app退出再进入/沉浸态上下滑时/锁屏/息屏/切多任务/拉通知栏/刷新上报)(暂停重新开始不上报） 增加场景： 1、上一个视频播完下一个自动开始播放 2、沉浸态上下滑开始自动播放（包括回看） 3、沉浸态内同一个视频重复播放不上报  信息流_单条内容_视频播放完成：（详情页退出/app退出//切多任务/拉通知栏跳走上报。重复

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| page | 操作所属页面 | string | 轻应用短剧详情页：lightapp_skit_detail 内流短剧详情页：inline_skit_detail |
| from_page | 操作上级页面 | string | 短剧选集页面：skit_episode_selection |
| feed_channel | 频道 | string | feed_channel='favourite' |
| item_position | 曝光位置 | number | 短剧沉浸态无此参数 |
| category_name | 频道 | string | 通过我的追剧观看的所有短剧category='favourite' |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| chapter_count | 短剧剧集数 | number | 短剧总集数(短剧有几集就报几集) |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| item_title | 内容标题 | string |  |
| play_location | 播放位置 | string | list（列表页）、detail（详情页） |
| e_ts | 事件发生时间 | number |  |
| req_id | 请求id | string |  |
| item_root_id | 沉浸态首个文章id | number |  |

**关联指标**: 浏览器信息流人均VV, 浏览器信息流消费DAU/日活
**关联页面**: 首页/推荐页, 首页, 沉浸式详情页, 短剧详情页

#### `content_item_video_over` — 信息流_单条内容_视频播放完成

**上报时机**: 信息流_单条内容_视频播放：视频播放时上报；多次播放多次上报；（退出再进入/app退出再进入/沉浸态上下滑时/锁屏/息屏/切多任务/拉通知栏/刷新上报)(暂停重新开始不上报） 增加场景： 1、上一个视频播完下一个自动开始播放 2、沉浸态上下滑开始自动播放（包括回看） 3、沉浸态内同一个视频重复播放不上报  信息流_单条内容_视频播放完成：（详情页退出/app退出//切多任务/拉通知栏跳走上报。重复

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| page | 操作所属页面 | string | 轻应用短剧详情页：lightapp_skit_detail 内流短剧详情页：inline_skit_detail |
| from_page | 操作上级页面 | string | 短剧选集页面：skit_episode_selection |
| feed_channel | 频道 | string | feed_channel='favourite' |
| item_position | 曝光位置 | number | 短剧沉浸态无此参数 |
| duration | 时长 | number |  |
| category_name | 频道 | string | 通过我的追剧观看的所有短剧category='favourite' |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| chapter_count | 短剧剧集数 | number | 短剧总集数(短剧有几集就报几集) |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| item_title | 内容标题 | string |  |
| play_location | 播放位置 | string | list（列表页）、detail（详情页） |
| e_ts | 事件发生时间 | number |  |
| req_id | 请求id | string |  |
| item_root_id | 沉浸态首个文章id | number |  |
| item_percent | 播放进度 | number | 本次播放过程的最大播放进度，拖动进度条也算，上限100 |
| length | 视频长度 | number | 单位毫秒 |

**关联指标**: 浏览器信息流人均VV, 浏览器信息流人均消费时长
**关联页面**: 首页/推荐页, 首页, 沉浸式详情页, 短剧详情页

#### `content_item_video_play_fail` — 播放失败

**上报时机**: 信息流_单条内容_视频播放：视频播放时上报；多次播放多次上报；（退出再进入/app退出再进入/沉浸态上下滑时/锁屏/息屏/切多任务/拉通知栏/刷新上报)(暂停重新开始不上报） 增加场景： 1、上一个视频播完下一个自动开始播放 2、沉浸态上下滑开始自动播放（包括回看） 3、沉浸态内同一个视频重复播放不上报  信息流_单条内容_视频播放完成：（详情页退出/app退出//切多任务/拉通知栏跳走上报。重复

**关联页面**: 沉浸式详情页, 短剧详情页, 首页/推荐页, 首页

#### `content_item_like` — 信息流_单条内容_点赞

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 短剧详情页, 首页/推荐页, 首页

#### `content_item_unlike` — 信息流_单条内容_取消点赞

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 短剧详情页

#### `content_item_share` — 信息流_单条内容_分享

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 短剧详情页

#### `content_item_collect` — 信息流_单条内容_收藏

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 短剧详情页

#### `content_item_notinteresting` — 信息流_单条内容_不感兴趣（拉黑作者）

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 首页/推荐页, 首页, 图文详情页, 沉浸式详情页, 短剧详情页

#### `content_item_report` — 信息流_单条内容_问题反馈（投诉）

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页, 短剧详情页

#### `content_item_comment` — 信息流_单条内容_评论

**上报时机**: 公共参数（只要page，不要from_page,module,from_module） 信息流通用参数（详情页触发的参数同条目的view事件，feed流上触发的参数同条目曝光事件） 信息流_单条内容_点赞：点赞成功时上报；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_取消点赞：取消点赞成功时；不去重 （包括详情页，小视频沉浸态） 信息流_单条内容_分享：点击分享渠道时；不去重 （包括详情

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| card_id | card_id非文章id | string | 运营位_专题卡片：cms里的配置id 运营位_banner:cms里的配置id |
| card_type | card类型 | string | _position |
| card_style | card样式 | string | 无图 news_nopic 大图 news_largepic 小图 news_ littlepic  组图3图 news_threepic 短视频内容统一上报video |
| card_item_position | card里item条目的顺序 | string | 0、1、2、3、4、5.....    从0开始 |
| duration | 时长 | number |  |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 |
| share_type | 分享渠道 | string | 微信/朋友圈/微博/更多 |
| feedback_type | 不感兴趣类型 | string | 拉黑作者：xx（原始文案） 不感兴趣：时政（原始文案） 屏蔽关键词：欧冠（屏蔽关键词为特殊情况，目前看到新时代、足球、财经频道有） |
| report_type | 投诉类型 | string | 重复/低俗/标题党/内容差 |
| comment_detail | 评论具体内容 | string | 哈哈哈哈 |
| comment_type | 主动评论/回复 | string | 主动/回复 |
| item_root_id | 根内容id
沉浸态首个文章id | string | toutiao_newhome_sjofhaowej19384 |
| item_root_type | 根内容id
沉浸态首个内容类型 | string | video、minivideo |
| item_from_id | 相关阅读来源文章id | string | 用户点击相关阅读进入下个详情页时上报，列表页点击不上报 |
| item_auto_play | 是否自动播放 | boolean | true/false |
| length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |
| fail_type | 失败类型 | string | play_start，播放开始失败（播放时长=0） play_middle，播放途中失败（播放时长>0） |
| backinfo | 负反馈透传参数 | string |  |
| play_location | string | 播放位置 | list（列表页）、detail（详情页） |
| expose_mode | 曝光方式 | string | back返回拦截至下滑一屏的曝光：back_holdup |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| xm_cache_status | 小米cdn缓存状态 | string |  |
| xm_cdn_prov | 小米cdn厂商 | string |  |
| xm_remote_address | 小米cdn服务端ip | string |  |
| bitrate | 码率 | string |  |
| video_resolution | 分辨率 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页, 短剧详情页

#### `content_duration` — 时长

**上报时机**: 1）详情页时长（图文、短视频、小视频记录）（离开这个页面上报，同触发view事件） 2）短视频/小视频播放时长（视频暂停，切多任务不累计时长，离开这个页面上报，同触发video_over事件） 3）频道时长只算在频道主流时长（记录用户在频道列表页时长，退出，进入详情页，切多任务上报） 息屏锁屏不上报

**关联指标**: 浏览器信息流人均时长, 浏览器信息流人均消费时长
**关联页面**: 首页/推荐页, 首页, 图文详情页, 沉浸式详情页, 短剧详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_count_item` — 内容曝光条数

**上报时机**: 1）从后台切换至前台开始计数 2）从前台切换至后台时上报累计曝光   切到后台定义：app退出桌面，锁屏/息屏/多任务切第三方/通知栏跳三方

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| expose_total | 总曝光条数 | 数值型 | 1，2，3…… |

**关联指标**: 信息流有效用户
**关联页面**: 首页/推荐页, 首页

#### `content_refresh` — 刷新

**上报时机**: 刷新接口返回上报（刷新只要page 不要from_page,module,from_module） 范围（不包括热榜）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| refresh_type | 刷新方式 | string | 下拉刷新：swipe_down 自动刷新：auto_refresh(包括点击频道刷新) 加载更多刷新：load_more 按钮刷新：button_refresh 底部tab点击刷新：bottom_ta |
| is_success | 是否刷新成功 | boolean | true/false |
| duration | 接口耗时(毫秒) | number |  |

**关联页面**: 首页/推荐页, 首页

#### `content_refresh_load` — 刷新_内容渲染

**上报时机**: 刷新接口返回后有内容曝光/内容渲染失败时上报（刷新只要page 不要from_page,module,from_module） 范围（不包括热榜）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| refresh_type | 刷新方式 | string | 下拉刷新：swipe_down 自动刷新：auto_refresh(包括点击频道刷新) 加载更多刷新：load_more（不用上报该事件） 按钮刷新：button_refresh 底部tab点击刷新： |
| is_success | 是否刷新成功 | boolean | true/false |
| duration | 加载耗时(毫秒) | number |  |

**关联页面**: 首页/推荐页, 首页

#### `content_item_request` — 信息流_内容请求

**上报时机**: 向服务端发起内容请求时上报，每请求一次上报一次事件

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| feed_channel | 频道 | string |  |
| item_count | 返回条数(内容) | number |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `content_follow` — 关注

**上报时机**: 关注成功时上报（包括详情页，关注流）（只要page），（module,from_page,from_module不需要）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key
content key | 公共属性
内容通用属性 | string |  |
| item_author | 作者名 | string |  |
| follow_source | 关注来源 | string | 图文详情页：content_detail_news 短视频详情页：content_detail_video 作者详情页：main_follow_author_detail 发现_关注页：main_fo |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页

#### `content_unfollow` — 取消关注

**上报时机**: 取消关注成功时上报（包括详情页，关注流）（只要page），（module,from_page,from_module不需要）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key
content key | 公共属性
内容通用属性 | string |  |
| item_author | 作者名 | string |  |
| follow_source | 关注来源 | string | 图文详情页：content_detail_news 短视频详情页：content_detail_video 作者详情页：main_follow_author_detail 发现_关注页：main_fo |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页

#### `content_channel_edit` — 编辑频道

**上报时机**: 编辑成功时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| all_channel | 保存时的保留channel列表 | string | ['main_follow','main_game','main_recommend'] |
| removed_channel | 移除的channel | string | ['main_zhihu','video_short','video_funny'] |

**关联页面**: 首页/推荐页, 首页

#### `content_button_show` — 取消关注

**上报时机**: 取消关注成功时上报（包括详情页，关注流）（只要page），（module,from_page,from_module不需要）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_author | 作者名 | string |  |
| follow_source | 取消关注来源 | string | 文章详情页：content_detail 关注流_我的关注：follow_follow_user |

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_export_show` — 引流曝光

**上报时机**: （露出即上报，滑走再滑会，露出后继续上报）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| export_type | 引流类型 | string | 按钮：button 弹窗：window 页面浮层：page |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_export_click` — 引流点击

**上报时机**: 点击即上报，点击多次上报多次

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| export_type | 引流类型 | string | 按钮：button 弹窗：window 页面浮层：page |

**关联页面**: 图文详情页, 沉浸式详情页, 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_slide` — 屏幕滑动

**上报时机**: 1、滑动停止时上报 2、滑动最大位置item_position变化时才上报 (优先做推荐流频道。如果可以复用，再扩展其他频道)

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_position | 滑动的最大位置 | number | 0、1、2、3、4、5.....    从0开始  （广告的位置不算） 沉浸态重点关注 |
| slide_orientation | 滑动方向 | string | up、down |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_fold_button_expose` — 详情页折叠按钮曝光，单页面只曝光1次，上下滑动不重复曝光，退出后再进入重复报

**关联页面**: 图文详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_fold_button_click` — 详情页折叠按钮点击，点击多次算多次

**关联页面**: 图文详情页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_video_over_exception` — content_item_video_over_exception

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | duration | number |  |

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_video_auto_play` — 信息流_单条内容_视频自动播放

**上报时机**: 信息流_单条内容_视频自动播放：推荐页首条内容第一次开始自动播放时上报，下划再上划自动播放/点进视频详情页退出自动播放均不上报 信息流_单条内容_视频自动播放完成：推荐页首条内容第一次开始自动播放结束时上报，第二次及之后播放完成不上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | 时长 | number |  |
| item_video_length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |

**关联指标**: 浏览器信息流人均VV
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `content_item_video_auto_over` — 信息流_单条内容_视频自动播放完成

**上报时机**: 信息流_单条内容_视频自动播放：推荐页首条内容第一次开始自动播放时上报，下划再上划自动播放/点进视频详情页退出自动播放均不上报 信息流_单条内容_视频自动播放完成：推荐页首条内容第一次开始自动播放结束时上报，第二次及之后播放完成不上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | 时长 | number |  |
| item_video_length | 视频长度 | number | 单位毫秒 |
| item_percent | 视频播放进度/图文浏览进度 | number | 退出后记录percent，百分比例如  0/1/50/100，保留整数；多次浏览记最大值 |

**关联指标**: 浏览器信息流人均VV
**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数, 信息流公共参数

#### `url_click` — 软广链接点击

**上报时机**: 多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| from_item_docid | 软文的item_docid | string |  |
| from_item_cp_name | 软文的item_cp_name | string |  |

**关联页面**: 图文详情页

**引用公共字段组**: 公共参数

#### `content_item_cover_load_fail` — 信息流_单条内容_封面加载失败

**上报时机**: 封面加载失败时上报，不重复上报 不考虑内容是否曝光

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| error_msg | 错误详情 | string |  |
| url | 内容url | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `content_duration_v2` — 信息流时长

**上报时机**: 以任何方式离开频道列表页上报，记录从进入频道列表页到离开频道列表页的时长； 离开频道场景： 退出频道、切换频道tab、进入详情页、退出APP（包含退出到后台）、息屏、锁屏

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| content key | 信息流通用属性中流的属性 | string |  |
| feed_channel | 频道 | string | 具体的频道值 |
| page | 页面 | string |  |
| duration_type | 时长类型 | string | feed_channel |
| duration | 时长 | number | 从进入频道页到离开频道页的时长 单位：毫秒 |
| ​common key | 公共属性 | string |  |
| content key | 信息流所有通用属性 | string |  |
| feed_channel | 频道 | string | 具体的频道值 |
| page | 页面 | string |  |
| duration_type | 时长类型 | string | detail_page |
| duration | 时长 | number | 从进入详情页到离开详情页的时长 单位：毫秒 |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |

**关联指标**: 浏览器信息流人均时长, 浏览器信息流人均消费时长
**关联页面**: 首页/推荐页, 首页, 图文详情页, 沉浸式详情页, 短剧详情页

### exception (异常事件)

#### `catch_exception` — 异常捕获事件

**上报时机**: 出现异常问题触发

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| catch_exception_detail | 异常捕获明细 | string |  |
| catch_exception_type | 异常捕获类型 | string | mmkv_init：mmkv初始化时异常； saveAdsToFile：广告数据序列化到文件的异常； getAdsFromFile：广告数据反序列化是的异常； video_play_fail:视频播放 |
| video_fail_stockid | 异常视频id | string | 视频播放id |
| filter_type | douyink:抖音直播
chuanshanjia：千川直播
ad：广告
content：内容 | string | douyink:抖音直播 chuanshanjia：千川直播 ad：广告 content：内容 |
| filter_position | 内容所处流中位置 | int |  |
| filter_reason | 异常过滤原因 | string | 下发内容、直播、广告过滤具体原因 |
| dy_init_status | 抖音直播初始化状态 | int | 0：初始化失败； 1：初始化成功； 2：初始化中（最终有概率无回调）； 3：未开始过初始化； |
| csj_init_status | 穿山甲初始化状态 | int | 0：初始化失败； 1：初始化成功； 2：初始化中（最终有概率无回调）； 3：未开始过初始化； |
| tt_api_live_state | 和直播sdk交互层的直播sdk状态 | int | -100： sdk未初始化完成 -5：默认状态 1：注册插件事件回调 2；开始执行初始化 3：执行初始化完成 4：初始化回调成功 5：初始化回调失败 |
| tt_live_state | 穿山甲sdk内部的直播sdk状态 | int | -100： sdk未初始化完成 |
| init_process | 是否为主进程 | boolean | true:为主进程 false:为子进程 |

**引用公共字段组**: 公共参数

#### `content_item_view_exception` — 浏览事件时长异常事件

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| duration | duration | number |  |

**引用公共字段组**: 公共参数, 信息流公共参数

#### `reset_server_url` — 重置服务端接口地址

**上报时机**: 代理域名达到最大连续失败数时上报

**引用公共字段组**: 公共参数

### growth (拉新拉活)

#### `thirdapp_response` — 第三方app忘川链接回传

**上报时机**: 调启忘川链接并响应时

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| mission_id | 任务id | string | 1，2，…… |
| response_data | 响应值 | string | 如“success” |
| request_data | 请求值 | string | 如https://wcp.taobao.com/adstrack/track.json?action=2&app=1&channel=2200803435073&oaid=2f85f9c1d727fc |

**引用公共字段组**: 公共参数

### incentive (激励体系)

#### `box_reward_expose` — 宝箱挂件曝光

**上报时机**: 曝光时上报，同页面反复出现不上报，频道及tab切换时不上报。 仅宝箱消失重新出现时上报（例如：详情页返回、切出内容中心back、锁屏重启等） （不需要page、frompage、module、from_module）

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `box_reward_click` — 宝箱挂件点击

**上报时机**: 点击及上报 （需要page，不需要frompage、module、from_module）

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `reward_point_expose` — 激励挂件曝光

**上报时机**: 曝光时上报，同页面反复出现不上报，频道及tab切换时需要上报。 仅宝箱消失重新出现时上报（例如：详情页返回、切出内容中心back、锁屏重启等） （需要page、frompage、module、from_module）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| point_name | 宝箱任务挂件 | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `reward_point_click` — 激励挂件点击

**上报时机**: 点击及上报 （需要page，不需要frompage、module、from_module）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| point_name | 宝箱任务挂件 | string |  |
| click_type | cancel/agree | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `convert_popup_window_expose` — 积分激励弹窗曝光

**上报时机**: 弹窗曝光即上报，弹出几次，上报几次。不去重 page、from_page、module、from_module为空

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| popup_type | reward_sign//金币-签到弹窗 | string |  |
| popup_source | 视频tab/我的/热榜/首页 | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `convert_popup_window_click` — 积分激励弹窗点击

**上报时机**: 点击取消，确定按钮即上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| popup_type | reward_sign//金币-签到弹窗（首页） | string |  |
| popup_source | 视频tab/我的/热榜/首页 | string |  |
| popup_click_type | cancel/agree | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

### livestream (直播间)

#### `sdk_start_load` — sdk开始初始化

**上报时机**: 用户开始初始化SDK时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| sdk_name | SDK名称 | string | douyin_sdk:抖音直播SDK newchuan_sdk：穿山甲新SDK chuan_sdk：穿山甲旧SDK |
| init_process | 是否为主进程 | boolean | true:为主进程 false:为子进程 |

**引用公共字段组**: 公共参数

#### `sdk_load_result` — sdk初始化结果

**上报时机**: 用户初始化SDK拿到结果上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| sdk_name | SDK名称 | string | douyin_sdk:抖音直播SDK newchuan_sdk：穿山甲新SDK chuan_sdk：穿山甲旧SDK douyin_live_plugindownload: 直播插件下载 douyin_ |
| init_process | 是否为主进程 | boolean | true:为主进程 false:为子进程 |
| duration | 加载耗时(毫秒) | number |  |
| is_success | 刷新成功 | string | ture/flase：初始化/下载/安装/加载成功与否 |
| error_msg | 错误类型 | string | 具体值 |

**引用公共字段组**: 公共参数

#### `enter_room` — 进入直播间

**上报时机**: 进入直播间内流时上报 离开直播间内流时上报 直播间关注成功时上报 直播间评论成功时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_count | 进入直播间次数 | number | 在直播间内流进入了几次直播间 |
| duration | 直播间停留时长（毫秒） | number |  |

**引用公共字段组**: 公共参数

#### `exit_room` — 离开直播间

**上报时机**: 进入直播间内流时上报 离开直播间内流时上报 直播间关注成功时上报 直播间评论成功时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_count | 进入直播间次数 | number | 在直播间内流进入了几次直播间 |
| duration | 直播间停留时长（毫秒） | number |  |

**引用公共字段组**: 公共参数

#### `follow_room` — 关注直播间

**上报时机**: 进入直播间内流时上报 离开直播间内流时上报 直播间关注成功时上报 直播间评论成功时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_count | 进入直播间次数 | number | 在直播间内流进入了几次直播间 |
| duration | 直播间停留时长（毫秒） | number |  |

**引用公共字段组**: 公共参数

#### `room_comment` — 直播间评论

**上报时机**: 进入直播间内流时上报 离开直播间内流时上报 直播间关注成功时上报 直播间评论成功时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_count | 进入直播间次数 | number | 在直播间内流进入了几次直播间 |
| duration | 直播间停留时长（毫秒） | number |  |

**引用公共字段组**: 公共参数

#### `provider_null` — 在我们获取对方服务时，如果获取空，则新增个点位

**上报时机**: 杀掉进程后快速上滑冷启，当抖音直播通过SDK打曝光点时，此时SDK未初始化完成，会上报此点位

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| from | 代表代码的场景 | string | 用于后续跟抖音研发对逻辑 |

#### `room_order` — 直播间下单

**上报时机**: 直播间下单支付成功时上报

**引用公共字段组**: 公共参数

#### `newhome_huoshan_room_load` — 火山直播间插件下载状态

**上报时机**: 火山直播间插件下载时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| return_status | 返回状态 | string | 三种状态（开始初始化、下载成功、下载失败） |
| errorMessage | 失败的信息 | string |  |

**引用公共字段组**: 公共参数

### me (我的页面)

#### `me_setting_click` — 个人中心点击

**上报时机**: 公共参数(只要page，from_page,module,from_module不需要) 点击生效后上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| function | 操作发生的功能模块 | 字符串 | 账号管理：me_info 关注：follow 收藏：favorite 点赞：like 浏览历史：history 全屏模式：all_screen_mode 字体设置：font_setting 刷新方式： |
| status | 操作后开关状态 | 字符串 | 下拉刷新_桌面上滑后两秒内下拉回到桌面：off；返回二次确认：off（功能模块刷新方式） 发现：推荐;视频：综合（功能模块默认频道） 个性化推荐：off;开启内容中心：off（功能模块关于） 搜索（功 |

**关联页面**: 我的页, 个人中心页

**引用公共字段组**: 公共参数

#### `me_setting_expose` — 个人中心模块曝光

**上报时机**: 公共参数(只要page，from_page,module,from_module不需要) 点击我的按钮/切换tab后，进入我的一级页面记录曝光。 用户一个进程内只上报一次曝光事件

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| function | 功能模块 | string | 账号管理：me_info 关注：follow 收藏：favorite 点赞：like 浏览历史：history 全屏模式：all_screen_mode 字体设置：font_setting 刷新方式： |

**关联页面**: 我的页, 个人中心页

**引用公共字段组**: 公共参数

### operation (运营位)

#### `operation_icon_expose` — 运营位icon曝光

**上报时机**: 完成露出即曝光，刷新后二次上报 垂类频道记得上报page公共参数main_olympic from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| icon_id | 活动id | string |  |
| icon_name | icon名称 | string | 火炬传递/东奥指南 |
| icon_type | icon类型 | string | tag/icon |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_icon_click` — 运营位icon点击

**上报时机**: 点击触发，点击几次上报几次 垂类频道记得上报page公共参数main_olympic from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| icon_id | 活动id | string |  |
| icon_name | icon名称 | string | 火炬传递/东奥指南 |
| icon_type | icon类型 | string | tag/icon |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_icon_view` — 运营位icon浏览

**上报时机**: 退出详情页上报，退出几次 垂类频道记得上报page公共参数所在页面 from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| icon_name | icon名称 | string | 火炬传递/东奥指南 |
| icon_type | icon类型 | string | tag/icon |
| duration | 运营位时长 | string |  |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_content_expose` — 运营位条目曝光

**上报时机**: 1、完成露出即曝光，刷新后二次上报 2、点击触发，点击几次报几次 3、退出h5页面上报，浏览页面退出时上报（包括app退出、返回上一级页面，息屏锁屏，切多任务/拉通知栏跳走都算，只要详情页看不到就记） 垂类频道记得上报page公共参数 from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| content_name | 条目名称 | string | cms后台配置运营位名称 |
| duration | 运营条目时长 | string | 仅view事件上报 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_content_click` — 运营位条目点击

**上报时机**: 1、完成露出即曝光，刷新后二次上报 2、点击触发，点击几次报几次 3、退出h5页面上报，浏览页面退出时上报（包括app退出、返回上一级页面，息屏锁屏，切多任务/拉通知栏跳走都算，只要详情页看不到就记） 垂类频道记得上报page公共参数 from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| content_name | 条目名称 | string | cms后台配置运营位名称 |
| duration | 运营条目时长 | string | 仅view事件上报 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_content_view` — 运营位条目浏览

**上报时机**: 1、完成露出即曝光，刷新后二次上报 2、点击触发，点击几次报几次 3、退出h5页面上报，浏览页面退出时上报（包括app退出、返回上一级页面，息屏锁屏，切多任务/拉通知栏跳走都算，只要详情页看不到就记） 垂类频道记得上报page公共参数 from_page,mudule,from_mudule不需要

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| content_name | 条目名称 | string | cms后台配置运营位名称 |
| duration | 运营条目时长 | string | 仅view事件上报 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_notice_activity_expose` — 通知左侧运营位曝光

**上报时机**: 1、露出即曝光，再次露出再次上报 2、点击触发，点击几次报几次 page,from_page,mudule,from_mudule都不需要，不上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| notice_name | 通知名称 | string | 0618小铃铛 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_notice_activity_click` — 通知左侧运营位点击

**上报时机**: 1、露出即曝光，再次露出再次上报 2、点击触发，点击几次报几次 page,from_page,mudule,from_mudule都不需要，不上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| notice_name | 通知名称 | string | 0618小铃铛 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_question_expose` — 投票曝光

**上报时机**: 露出即曝光，曝光过后上下滑不上报 （33%内容曝光与内容曝光统一）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| question_id | 问卷id | string |  |
| question_name | 问卷名称 | string | 你喜欢内容中心吗？ |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `operation_question_click` — 投票点击

**上报时机**: 点击成功后上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| question_id | 问卷id | string |  |
| question_name | 问卷名称 | string | 你喜欢内容中心吗？ |
| question_option | 问卷选中项 | string | 超级喜欢 |

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

### search (搜索相关)

#### `search_click` — 搜索框点击

**上报时机**: 点击时（不需要page、frompage、module、from_module不需要）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |

**关联页面**: 搜索首页, 首页/推荐页

#### `novel_search_click` — 小说搜索框点击

**上报时机**: 点击时上报，多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |

**关联页面**: 首页/推荐页, 首页

#### `search_security` — 搜索_安全网址

**上报时机**: 请求安全网址时

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| from_page | 上级页面 | string | 从浏览器首页搜索框产生的搜索，from_page=browser 从搜索结果页换query产生的搜索，from_page=search_result |
| is_baidu_sdk | 是否百度sdk | boolean | 0：原h5；1：百度sdk |
| searchengine_id | 搜索引擎配置模版 | string | cms中配置的引擎模版 |
| searchengine_channelid | 搜索引擎渠道号 | string | 百度：from参数（1012852u等） 360：srcg参数（ff_xiaomi_4等） 搜狗：bid参数或pid参数（sogou-mobp-6018df1842f7130f等） 头条：origin |
| search_enter_way | 进入搜索的方式 | string | 信息流 首页 第三方app调起 rs 名站 长按菜单键 底tab搜索 下滑（简洁版下） |
| search_way | 搜索方式 | string | widget 热榜 名站（我的页面-点击百度icon） 书签 三方调起搜索 搜索框输入 sugword 历史记录 搜索发现 预置词 搜索框提示词 文末rs 切换搜索引擎 阅后rs |
| query | 搜索词 | string |  |
| third_packagename | 第三方调起包名 | string | app_launch_way等于“第三方调起”时，上报第三方调起包名，其余情况为空 |
| device_id | device_id | string |  |
| network | 网络类型 | string | WIFI/5G/4G/3G/2G/ETHERNET/NONE/UNKNOWN |
| app_version | APP版本 | string |  |
| os_version | 系统版本 | string |  |
| stable | 版本类别 | string |  |
| miui_version | MIUI版本 | string |  |
| model_name | 设备名称 | string |  |
| androidid | 安卓_id | string |  |

#### `search_homepage_expose` — 搜索首页曝光

**上报时机**: 只要进入或回到搜索首页都记，包括从浏览器内其他页面进入或返回，以及从系统内其他地方进入（点击桌面icon进入、从其他app返回、其他app调起、拉回通知栏、从多任务进入、屏幕解锁、点击桌面书签进入）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| page_type | 首页类型 | string | from_desktop（针对具备应用建议和热榜功能的首页） new_search_homepage：新版搜索首页 old_search_homepage:旧版搜索首页 |
| search_homepage_enter_way | 进入搜索首页的方式 | string | home_page：首页搜索框 feed：资讯信息流 search_detail_page：sug页返回 web_page：普通网页（包括点击宫格名站里的百度） menu：长按菜单 gongge：宫格 |

**引用公共字段组**: 公共参数

#### `search_homepage_module_expose` — 搜索首页模块曝光

**上报时机**: 1、item漏出三分之一记曝光（图片icon+文字一起算三分之一） 2、我的书签最多曝光前20个 3、如下不曝光：未在视线范围内出现的（包括键盘挡住的）、隐藏了的卡片、未展开的搜索历史 4、如下反复操作不重复曝光：页面反复上下滑动、展开收起（搜索历史）、隐藏展开（我的书签和经常访问）、键盘收起弹出、 5、滑动过程中不曝光，停止了才曝光 6、只要再次回到该页面都进行重新曝光，包括从浏览器内其他页面进

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| page_type | 首页类型 | string | from_desktop（针对具备应用建议和热榜功能的首页） new_search_homepage：新版搜索首页 old_search_homepage:旧版搜索首页 |
| search_homepage_enter_way | 进入搜索首页的方式 | string | home_page：首页搜索框 feed：资讯信息流 search_detail_page：sug页返回 web_page：普通网页（包括点击宫格名站里的百度） menu：长按菜单 gongge：宫格 |
| card_type | 卡片类型 | string | 网址 剪贴板 搜索历史 我的书签（只打前20个） 经常访问 应用建议 今日热搜 预置词 搜索发现 小说榜单 猜你想搜 |
| novels_list_type | 小说热榜类型 | string | 当模块类型为小说榜单时上报，否则为空 boy：男生 girl：女生 |
| card_position | 模块位置 | number | 0、1、2…… |
| item_title | item标题 | string | 网址为网址的标题 剪贴板为复制的内容 搜索历史为搜索词 我的书签为每条书签的标题 经常访问为每个item的标题 应用建议为应用名 今日热搜为热词 预置词为每个item标题 搜索发现为每个item标题  |
| item_value | item的value | string | 应用建议为应用包名 其他情况值为空 |
| card_item_position | 模块内位置 | number | 0、1、2…… |

**引用公共字段组**: 公共参数

#### `search_homepage_module_click` — 搜索首页模块点击

**上报时机**: 无去重逻辑 多次点击多次上报 删除、清空、隐藏、展示操作后引起了位置的变动，后续的位置以真实位置为准上报，前面的已经打过点的不改变，均以当下真实的位置上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| page_type | 首页类型 | string | from_desktop（针对具备应用建议和热榜功能的首页） new_search_homepage：新版搜索首页 old_search_homepage:旧版搜索首页 |
| search_homepage_enter_way | 进入搜索首页的方式 | string | home_page：首页搜索框 feed：资讯信息流 search_detail_page：sug页返回 web_page：普通网页（包括点击宫格名站里的百度） menu：长按菜单 gongge：宫格 |
| card_type | 模块类型 | string | 网址 剪贴板 搜索历史 我的书签 经常访问 应用建议 今日热搜 键盘_书签 键盘_剪贴板 键盘_无痕浏览 预置词 搜索发现 小说榜单 猜你想搜 |
| novels_list_type | 小说热榜类型 | number | 当模块类型为小说榜单时上报，否则为空 boy：男生 girl：女生 |
| card_position | 模块位置 | string | 0、1、2…… 键盘类为空 |
| item_title | item标题 | string | 网址为网址的标题 剪贴板为复制的内容 搜索历史为搜索词 我的书签为每条书签的标题 经常访问为每个item的标题 应用建议为应用名 今日热搜为热词 键盘类为空 预置词为每个item标题 搜索发现为每个i |
| item_value | item的value | string | 应用建议为应用包名 键盘类为空 |
| card_item_position | 模块内位置 | number | 0、1、2…… 键盘类为空 |
| item_type | item类型 | string | common |
| click_area | 点击位置 | string | 复制（网址） 编辑（网址） 二维码（网址） 搜索词（搜索历史） 删除（搜索历史、应用建议） 清空（搜索历史） 默认（我的书签/经常访问、点击每个item、应用建议、全网热榜、键盘_书签、键盘_剪贴板、 |

**引用公共字段组**: 公共参数

#### `search_sugpage_expose` — 搜索sug页曝光

**上报时机**: 1、sug页每刷新一次即上报一次，即考虑连续输入 2、只要再次回到该页面都进行重新曝光，包括从浏览器内其他页面进入或返回，以及从系统内其他地方进入（点击桌面icon进入、从其他app返回、其他app调起、拉回通知栏、从多任务进入、屏幕解锁、点击桌面书签进入）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| query | 搜索词 | string | 用户的搜索词 |
| searchid | searchid | string | 每一次即搜生成唯一id |

**关联页面**: 搜索SUG页

#### `search_sugpage_module_expose` — 搜索sug页模块曝光

**上报时机**: 前端上报 1、item漏出三分之一记曝光（图片icon+文字一起算三分之一） 2、我的书签最多曝光前20个 3、如下不曝光：未在视线范围内出现的（包括键盘挡住的） 4、如下反复操作不重复曝光：页面反复上下滑动、键盘收起弹出 5、滑动过程中不曝光，停止了才曝光 6、只要再次回到该页面都进行重新曝光，包括从浏览器内其他页面进入或返回，以及从系统内其他地方进入（点击桌面icon进入、从其他app返回、其

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| req_id | 请求id | string | 每次请求的唯一标识 |
| project_rev | 前端版本 | string |  |
| card_type | 卡片类型
（卡片的一级分类） | string | app：游戏 / 应用 product：小米有品 / 小米商城 video：小米视频 book：浏览器小说   website：网址   box：快递/ 彩票/ 天气 sugword：sugword  |
| item_type | item类型
（卡片的二级分类） | string | card_type='app'时： gamecenter_app：游戏 app：应用  card_type='product'时： mi_product：小米商城商品 youpin_product：小 |
| item_template | 卡片样式
（卡片具体的样式） | string | card_type='app' & item_type='gamecenter_app'时： top-game-banner：游戏大卡下载 top-game-banner-order：游戏大卡预约 t |
| item_value | item_value | string | card_type为app时，记录应用包名 其他情况值为空 |
| item_exp_id | 游戏实验id | string | sug为游戏类型时需要展示游戏实验id，其他情况为空 |
| alg_exp_id | 检索端实验id | string |  |
| sug_exp_id | 融合实验id | string | 各种实验ID的融合 |
| item_id | item id | string | 索引库里的每条数据的id，包含游戏id 本机应用和设置为空 |
| item_title | item标题 | string |  |
| item_position | 模块位置 | number | 每个item的位置，（未展开的位置也计算在内，但未展开前无实际曝光） 0、1、2…… |
| card_item_position | 模块内位置 | number | item在模块中的位置 0、1、2…… |
| query | 搜索词 | string |  |
| searchid | searchid | string | 每一次即搜生成唯一id |

**关联页面**: 搜索SUG页

#### `search_sugpage_module_click` — 搜索sug页模块点击

**上报时机**: 前端上报 无去重逻辑 多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| req_id | 请求id | string | 同上 |
| project_rev | 前端版本 | string |  |
| card_type | 模块类型 | string |  |
| item_type | item类型 | string |  |
| item_template | 卡片样式 | string |  |
| item_value | item_value | string |  |
| item_exp_id | 实验id | string |  |
| alg_exp_id | 检索端实验id | string |  |
| sug_exp_id | 融合实验id | string |  |
| item_id | item id | string |  |
| item_title | item标题 | string |  |
| item_position | 模块位置 | number |  |
| card_item_position | 模块内位置 | number |  |
| query | 搜索词 | string |  |
| searchid | searchid | string |  |
| click_area | 点击位置 | string | 安装（应用） 下载（应用） 打开（应用） 预约（应用） 已预约（应用） 阅读（小说） 大图（小米商品） 商品（小米商品） 播放（视频） 打开（商品） query（sugword） 上框（sugword |

**关联页面**: 搜索SUG页

#### `search_result_item_expose` — 搜索结果页内容曝光

**上报时机**: 内容露出1/3时上报，同一用户根据内容id去重，不重复上报 多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_type | 媒体类型 | string | 词条，广告，大家还在搜 |
| url | 网址 | string |  |
| query | 搜索词 | string |  |

**关联页面**: 搜索结果页

**引用公共字段组**: 公共参数

#### `search_result_item_click` — 搜索结果页内容点击

**上报时机**: 内容露出1/3时上报，同一用户根据内容id去重，不重复上报 多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| item_type | 媒体类型 | string | 词条，广告，大家还在搜 |
| url | 网址 | string |  |
| query | 搜索词 | string |  |

**关联页面**: 搜索结果页

**引用公共字段组**: 公共参数

#### `baidu_sdk_tab_click` — 百度sdk中tab点击

**上报时机**: 点击时上报，多次点击多次上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| function | 功能名称 | string | 全部/视频/资讯/热议/问答/文库/贴吧/图片/小视频/音乐/应用/购物/地图/采购/小说/用户/直播/笔记/下一页 |

**关联页面**: 搜索结果页

**引用公共字段组**: 公共参数

#### `baidu_sdk_exit` — 百度sdk退出

**上报时机**: 离开百度sdk时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| commen key | 公共属性 | string |  |
| duration_type | 时长类型 | string | 从任何场景发起搜索开始计时，离开sdk结束计时： quit：直接home退到后台 home：返回浏览器界面（非百度sdk页面） add_window：新建窗口 lock：锁屏 push：点击push跳 |
| duration | 时长 | number | 单位：毫秒 |

**关联页面**: 搜索结果页

#### `baidu_applet_sling` — 小程序调起

**上报时机**: 调起百度小程序时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| commen key | 公共属性 | string |  |
| is_baidu_sdk | 是否百度sdk | boolean | 0：原api；1：百度sdk |

#### `appbundle_download` — appbundle 安装

**上报时机**: appbundle开始下载时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| commen key | 公共属性 | string |  |
| is_success | 是否下载成功 | string | success:安装成功 fail：安装失败 |

### skit (短剧)

#### `content_item_uncollect` — 信息流_单条内容_取消追剧

**上报时机**: 信息流_单条内容_取消追剧：取消追剧成功时上报；不去重 （包括详情页，小视频沉浸态）

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_title | 内容标题 | string |  |
| category_name | 频道 | string |  |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

#### `episode_click` — 短剧选集

**上报时机**: 用户操作选集时，点击剧集选项时上报；点击未解锁的剧集也上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_type | 内容类型 | string | skit |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | string | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| chapter_count | 短剧剧集数 | number | 短剧总集数(短剧有几集就报几集) |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |
| click_scene | 点击场景 | string | 内流按钮：inline_skit 选集面板按钮：episode_selection |
| click_position | 点击位置 | string | 内流下按钮： next_episode 下一集按钮 episode_select 选集按钮 选集面板按钮： skit_summary 剧集简介 episode_select 选集 剧集合集数字，如“1 |

#### `selection_pageview` — 选集页面展示

**上报时机**: 进入选集页面有内容展示时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| page | 操作所属页面 | string | chapter_selection |
| item_type | 内容类型 | string | skit |
| item_docid | 内容id | string | 短剧为剧集id |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |

#### `ad_video_over` — 广告播放完成

**上报时机**: 短剧广告为穿山甲广告，穿山甲回调播放完成时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| item_docid | 内容id | string | 被解锁剧集的剧集id |
| tag_id | 广告位 | string | tag_id='1.132.1.20' |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| category_name | 频道 | string |  |
| req_id | 请求id | string |  |
| duration | 时长 | number | 单位毫秒 |
| item_video_length | 广告长度 | number | 单位毫秒 |
| item_percent | 广告播放进度 | number | 播放完成后记录percent，百分比例如  0/1/50/100，保留整数； |
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 竖版视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_url | 广告落地页 | string | http://....（h5或deeplink） |
| ad_brand | 广告主 | string | 头条/拼多多 |
| ad_feedback_type | 反馈类型 | string | 不感兴趣/出现过于频繁/内容质量差 |
| ad_click_area | 点击区域 | string | 广告区/按钮/标签区/左滑/滑动区 |
| ad_click_button_type | 点击按钮类型 | string | 应用下载/查看详情/立即跳转...... |
| request_status | 请求状态 | bool | true/false |
| request_error_info |  | string | 请求成功报null，失败报错误码【仅穿山甲】 |
| app_status | app安装状态 | string | installed/notInstalled |
| ad_img_count | 图片数量 | int | 0，1，2，3，4 |
| ad_return_type | 广告填充类型 | string | normal/flexible/add/back/screen_off |
| ad_position | 广告曝光的位置 | int | 1，2，3，4.... |
| page_number | 页码 | int | 0，1，2，3，4.... |
| ad_req_id | 广告请求id | string |  |
| positionId（新增） | 广告下发位置 | int | 1，2，3，4.... |
| Pagenum（新增） | 广告刷次 | int | 0，1，2，3，4.... |
| is_insert_middle_ad | 是否中插广告 | boolean | true：中插广告 false |
| duration | 时长 | number | 单位毫秒 |
| item_video_length | 广告长度 | number | 单位毫秒 |
| item_percent | 广告播放进度 | number | 播放完成后记录percent，百分比例如  0/1/50/100，保留整数； |
| item_root_id | 沉浸态首个文章id | string | 沉浸式及小视频内流从第二个播放内容开始之后每个内容（包括广告）都需要记录此值，值为第一个内容的id |
| root_cp_name | 沉浸态首个内容的内容提供方标识 | string |  |
| is_click_content_enter | 是否点击内容进入沉浸态 | boolean | true：点击内容进入沉浸态（push、推荐页插卡、相关推荐视频插卡） false |
| is_high_value | 是否高价值（激励广告） | boolean | true false |
| duration | 时长 | number | 单位毫秒 |
| item_video_length | 广告长度 | number | 单位毫秒 |
| item_percent | 广告播放进度 | number | 播放完成后记录percent，百分比例如  0/1/50/100，保留整数； |
| ad_exp_id | 广告实验id | string | 对应experimentld |
| ad_exp_id_list | 广告实验idlist | string | 对应adExpldlList |
| tag_id | 广告位 | string | BI里的id: 1.132开头 |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 |
| ad_source | 广告来源 | string | 小米 聚合穿山甲 |
| ad_style | 广告内容类型 | string | 小米小图 小米大图 小米组图 小米应用下载小图 小米应用下载大图 小米应用下载组图 小米视频广告 小米搜索广告卡片 穿山甲图片 穿山甲视频 |
| ad_id | 广告id | string | 广告素材的唯一标识 |
| ad_brand | 广告主 | string | 头条/拼多多 |
| ad_img_count | 图片数量 | int | 0，1，2，3，4 |
| ad_return_type | 广告填充类型 | string | normal：正常广告位 flexible：灵活广告位（补填充，当tag1/tag2无返回时） add：新增补充广告位（当内容返回条数>8条时，四插一） |
| ad_position | 广告曝光的位置 | int | 广告在列表中的绝对位置，广告的位置（不考虑内容） |
| page_number | 页码 | int | 0，1，2，3，4.... |
| ad_req_id | 广告请求id | string |  |

**引用公共字段组**: 公共参数, 公共参数

#### `ad_unlock_success` — 广告解锁成功

**上报时机**: 短剧剧集解锁成功时上报；回调穿山甲“奖励发放”状态

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| is_continuous | 是否连续 | boolean | true/false |
| item_docid | 内容id | string | 被解锁剧集的剧集id |
| tag_id | 广告位 | string | tag_id='1.132.1.20' |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id；为解锁而出激励广告的那一集 |
| order | 第几集 | number | 集数顺序（第一集就是1）；为解锁而出激励广告的那一集 |
| category_name | 频道 | string |  |
| req_id | 请求id | string |  |

#### `ad_unlock_pageview` — 短剧广告解锁蒙层-页面展现

**上报时机**: 提示观看短剧解锁的蒙层曝光时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| item_docid | 内容id | string | 被解锁剧集的剧集id |
| tag_id | 广告位 | string | tag_id='1.132.1.20' |
| category_name | 频道 | string |  |
| req_id | 请求id | string |  |

#### `ad_unlock_click` — 短剧广告解锁蒙层-点击广告解锁

**上报时机**: 点击确认观看短剧解锁蒙层

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| ​common key | 公共属性 | string |  |
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| item_docid | 内容id | string | 被解锁剧集的剧集id |
| tag_id | 广告位 | string | tag_id='1.132.1.20' |
| category_name | 频道 | string |  |
| req_id | 请求id | string |  |

#### `enter_skit_inner` — 点击进入短剧内流

**上报时机**: 任何点击进入短剧轻应用时上报

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| book_id | 短剧id | number | 短剧id |
| chapter_id | 剧集id | number | 剧集的id |
| order | 第几集 | number | 集数顺序（第一集就是1） |
| req_id | 请求id | string |  |
| skit_source | 短剧来源 | string | 不管什么场景都固定上报feed |
| is_skit_inner | 是否短剧内流 | number | 1（feed_alg_source=toutiao且page=lightapp_skit_detail上报） 0（其余场景都报0） |
| category_name | 头条频道名称 | string | 刷新展示的卡片：跟随首页推荐现有频道"___all___" 横划后加载的卡片：hotsoon_skit_feed_card 横划进入纯短剧内流的卡片：hotsoon_skit_detail_draw  |

### tab (tab标签)

#### `tab_top_click` — 顶tab点击（滑动）

**上报时机**: 顶tab滑动，点击上报。当前频道下点击多次不上报（上滑进入首次刷新，不计） （只要page就行。不要module，from_module，from_page） 范围包括热榜

**关联页面**: 首页/推荐页, 首页

**引用公共字段组**: 公共参数

#### `tab_bottom_click` — 底tab点击

**上报时机**: 底点击上报，点击多次上报多次（上滑进入首次刷新，不计） （只要page就行。不要module，from_module，from_page） 范围包括热榜，小说

**关联页面**: 首页/推荐页, 首页, 个人中心页, 我的页

**引用公共字段组**: 公共参数

---

## 公共字段定义

### 预置参数
内容中心onetrack 预置参数

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| imei1 | imei1 MD5值 | string | 空的 |
| roaid | 系统OAID | string |  (从系统直接取的oaid，下面的oaid逻辑是（先读缓存、再读系统）) |
| oaid | OAID | string |  (MIUI V10.2稳定版后支持，目前MIUI日活中覆盖率约为80%) |
| android_id | Android ID | string |  |
| instance_id | 匿名ID | string | app级别id（卸载app，id会变） (app级别（卸载app，id会变）) |
| uid | 账号id | string | 小米账号 |
| session_id | session_id | string | app退出重置（目前o2o现状app退出跟下一次启动一致） (退回到桌面/切多任务/通知栏消息跳三方时session_id会变； 锁屏息屏，下拉通知栏时sessi) |
| ip | ip | string |  |
| region | 地区 | string |  (用户设置的国家/地区) |
| model | 设备名 | string |  |
| platform | 平台 | string |  |
| miui | MIUI版本号 | string | 举例：12.10.1.2 |
| build | 版本类型 | string | S：稳定版 D： 开发版 A：体验版 空值：用户自己编的版本 |
| os | 系统版本号 | string |  (安卓版本号) |
| app_ver | APP版本号 | string |  |
| e_ts | 事件发生时间 | number | 本地客户端时间 |
| net | 网络 | string | WIFI/5G/4G/3G/2G/ETHERNET/NONE/UNKNOWN NONE:没有联网， UNKNOWN:未知类型， ETHERNET:电视有线网 |
| sdk_ver | SDK版本号 | string |  |
| app_id | APPID | string |  |
| pkg | 包名 | string |  |
| channel | 渠道 | string | 一般为业务分发的渠道，比如抖音、应用宝等，用以跟踪渠道效果 |
| sdk_mode | SDK接入模式 | string | App模式（默认）/SDK模式（如小米账号SDK接入）/插件模式（如米家/快应用插件） |
| ot_ua | useragent | string |  |
| ot_privacy_policy | 隐私策略设置 | string | 打点时的隐私策略，取值范围为custom_open，custom_close，exprience_open，exprience_close |
| event | 事件名称 | string |  |
| ot_first_day | 用户是否是第一天访问 | boolean | true/false (如果用户清除数据后，再打开依然会被计为第一天;该值不绝对等同于新增激活 首次调起内容中心（不计是否通) |

### 公共参数
内容中心onetrack 公共参数

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| version_code | app_版本号 | number |  |
| device_id | 设备id | string | 优先取imei1md5 imei取不到取oaid原值（3.8版本以下是oaidmd5，3.8以上时oaid原值） (沿用目前newhome的设置) |
| imei2 | imei2md5值 | string |  (为方便之后与浏览器做映射) |
| is_first_today_imei | 是否为新用户(新imei服务端口径) | boolean | true/false |
| is_first_today_imei_expose | 是否为新曝光用户（首次信息流内容曝光业务口径） | boolean | true/false |
| city | 设置了本地频道的城市 | string | 有本地频道才会上报该值 |
| model_name | 机型名称 | string | 中文的机型名称，例如：Redmi 10 (https://husky.pt.miui.com/device/info   @Junjie1 L) |
| price_level | 机型分类 | string | 低端机，中端机，中高端机，高端机 |
| eid | 旧实验id | string |  |
| new_eid | 新实验id | string | 服务端下发的新实验id |
| is_decouple | 是否解耦 | boolean | 解耦：true 非解耦：false |
| app_launch_type | 启动方式 | string | 冷启动：cold_start 热启动：hot_start (冷启：后台没有内容中心进程，首次进入APP：上滑和PUSH 热启：后台有内容中心进程，APP内HOM) |
| app_launch_way | 进入内容中心方式(app启动级别) | string | Push推送进入：push 负一屏进入：assistant 桌面上划进入：launch_swipe 小部件: widget_4*2hot，widget_4*2r (app启动由哪种方式调起的，后续行为只要app没有退出，都算启动方式调起 4*4 热点资讯：widg) |
| app_type | 产品类型 | string | mcc：常规版 mcc_Breaking：精选版 mcc_recreation：娱乐中心 mcc_explore：首页改版 |
| page | 操作所属页面 | string | 页面频道模块参数汇总 (当前操作页面 短视频沉浸第一个也报沉浸态) |
| from_page | 操作上级页面 | string | 页面频道模块参数汇总 |
| module | 操作当前页面所属模块 | string | 页面频道模块参数汇总 |
| from_module | 操作上级页面所属模块 | string | 页面频道模块参数汇总 |
| login_miaccount | 小米账号是否登录 | boolean | true/false |
| resolution | 设备屏幕分辨率 | string | 宽*高 示例：720*1520 |
| carrier | 运营商 | string | 中国移动:yidong 中国联通:liantong 中国电信:dianxin 中国广电：guangdian 获取不到的打unknown |
| ram_info | 运行内存 | string | 5g 4g 3g |
| hard_disk_info | 机身存储 | string | 128g |
| province | 省份 | string |  |
| ext | 拓展字段 | string | everyday接口调（每隔12个小时），和内存逻辑一致 后续纯服务端计算的字段不需要客户端发版 (应用场景：对于特定用户属性的数据分析 比如过去30天没有曝光但今日活跃（流失回流用户） app_nl) |
| refresh_way | 刷新方式 | string | pull/button/pull_and_button (内容中心设置中的刷新方式) |
| default_channel | 默认频道 | string | play |
| personnal_recommend | 个性化推荐开启 | string | on/off |
| sys_personal_ad_recommend | 系统广告个性化推荐开启 | string | on/off |
| personal_ad_recommend | 个性化广告推荐开启 | string | on/off |
| server_user_id | 服务端用户id | string |  |
| top_style | 内容中心模式 | string | original/ transparent (经典模式/透明模式) |
| dp_ext | dp拓展字段 | string | has_guide&source_&pic_id_&is_ad_&channel_id_&father_channel_id_&ext_&url_&doc_id (如果来自deeplink方式，需打上dp的渠道号以及素材号，browser-aaa) |
| first_app_launch_way | 首次打开/激活渠道 | string | launch_swipe/push/douyin233/kuaishou233/...... (分上滑：launch_swipe push：push 拉新激活渠道：douyin233/kuaish) |
| today_first_enter_way | 当天首次激活方式 | string | launch_swipe/push/douyin233/kuaishou233/...... (分上滑：launch_swipe push：push 拉新激活渠道：douyin233/kuaish) |
| is_normal_mode | 是否标准版 | boolean | true/false (基础模式临时加的点，用来统计用户规模，正式版本中不需要) |
| screen_rotation | 屏幕旋转开启 | string | on/off |
| is_first_today_agree_cta | 当天是否首次同意CTA | boolean | true/false |
| is_all_screen | 是否全面屏 | string | true/false |
| login_douyin_account | 抖音账号是否登录 | boolean | true/false (用户点击我的账号之后，才会重新请求，若未点击则保持之前的缓存数据) |
| back_reconfirm | 返回二次确认是否开启 | string | on/off |
| launch_channel | 冷启动默认频道 | string |  |

### 信息流公共参数
信息流内容通用属性

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| feed_channel | 频道 | string | 页面频道模块参数汇总 (新定义 在该频道下发生的内容消费均打上该频道) |
| item_author | 作者 | string |  |
| item_docid | 内容id | string | like “toutiao_newhome_%%%%” |
| item_url | 内容url | string |  |
| item_title | 内容标题 | string |  |
| item_category | 一级分类 | string |  |
| item_subcategory | 二级分类 | string |  |
| item_cp_name | cp名称 | string |  |
| item_publish_time | 发布时间 | number |  |
| item_type | 内容类型 | string | 图文：news 视频：video 小视频：minivideo 直播：livestream 短剧：skit |
| item_position | 曝光位置 | number | 0、1、2、3、4、5.....    从0开始  （广告的位置不算） 沉浸态重点关注：点击推荐页小视频进入沉浸态，该小视频报在推荐页的位置，此后下滑位置依次从 (list_position) |
| item_order | 所有条目横向顺序 | number | 0、1、2、3、4、5.....    从0开始 (仅小视频推荐卡片/专题卡片上报 有则上报没有则不上报) |
| item_style | 内容样式 | string |  |
| view_type | 内容展示样式 | string | item_video_reco_right 相关推荐短视频 item_news_text_left_top 新闻无图样式,左侧置顶 item_video 大图短 (5.8版本带出，研发用的参数) |
| feed_alg_source | 流量来源 | string | 快手/互三/大数据/头条 (用户维度非内容维度) |
| minivideo_alg_source | 小视频流量来源 | string | 快手/互三/大数据/头条 (用户维度非内容维度) |
| page_number | 刷次 | int | 所需要的事件：以下事件只要有触发，就上报此参数。 请求页面数 流上正常上报，头条第几次返回的内容page_number就是几 二级页相关推荐目前都可以报1，后贴 |
| dp_ext | 内容拓展字段 | string | 服务端跟随内容一起下发，客户端再报上去 (接口场景：各个feed流（包括推荐，关注，视频等等）、详情页（相关推荐）、小视频沉浸态、短视频沉浸态) |
| req_id | 头条请求id | string |  (需要服务端回传) |
| category_name | 头条频道名称 | string | 头条category中英文对照表 (需要服务端回传) |
| toutiao_user_id | 头条匿名id | string |  (需要服务端回传) |
| item_authorid | nh侧作者id | string |  |
| item_cpauthorid | cp侧作者id | string |  |
| img_count | 图片数量 | number |  |
| word_count | 文字数量 | number |  |
| item_return_type | 内容填充类型 | string | normal：正常内容 flexible：灵活内容 (灵活内容位需求已删除) |
| expose_position | 灵活内容曝光位置 | string | 0、1、2、3、4、5.....    从0开始  （广告的位置不算） 正常内容的expose_position=item_position，灵活内容的expo |
| page_origin | 场景入口标识 | string | main_recommend：推荐流小视频卡片 content_detail_news：图文场景相关推荐小视频插卡 content_detail_video：视 |
| global_position | 全局位置 | int | 包括信息流+广告的全局位置 |

---

*此文件由 `generate_readme.py` 从 `event_tracking.db` 自动生成，如需更新请重新运行脚本*