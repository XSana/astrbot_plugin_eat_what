# eat_what · AstrBot 插件

一个根据关键词自动推荐「吃什么 / 喝什么」的 AstrBot 插件。  
支持关键词触发、随机推荐、食物素材管理，并自动处理图片格式。

---

## ✨ 功能特性

- 自动识别关键词并回复推荐内容  
- 支持 *食物 (food)* 与 *饮料 (drink)* 分类  
- 图片自动保存为 JPG：
  - 任意格式 → JPG  
  - 透明背景自动转白底  
  - 宽度超过 500 自动等比缩放到 500  
- 支持添加 / 删除条目  
- 自动从消息或引用消息中提取图片  
- 数据持久化，重启不丢失  

---

## 📌 指令说明

### 添加条目（管理员）

```
eat_what add <food|drink> <名称>
```

> 必须附带 1 张图片（消息本身或引用消息均可）

示例：

```
eat_what add food 拉面
eat_what add drink 奶茶
```

---

### 删除条目（管理员）

```
eat_what del <food|drink> <名称>
```

示例：

```
eat_what del drink 奶茶
```

---

### 查看列表

```
eat_what list <food|drink>
```

示例：

```
eat_what list food
eat_what list drink
```

---

## 🤖 自动推荐触发

当用户消息中包含配置中的关键词时：

- 命中「吃」相关关键词 → 从 `food` 中随机推荐  
- 命中「喝」相关关键词 → 从 `drink` 中随机推荐  

机器人会发送：

- 一张食物 / 饮料图片  
- 一条文本：`推荐你吃/喝 <名称>`

---

## ⚙ 配置说明

在插件配置中填写：

- `eat_keywords`：触发吃东西推荐的关键词列表  
- `drink_keywords`：触发喝东西推荐的关键词列表  

示例（JSON）：

```json
{
  "eat_keywords": ["吃什么", "午饭吃啥", "晚饭吃啥"],
  "drink_keywords": ["喝什么", "奶茶推荐", "想喝点东西"]
}
```

---

## 📁 数据与资源目录

插件会在 AstrBot 数据目录中创建自己的资源目录，例如：

```
astrbot_data/
  plugins/
    astrbot_plugin_eat_what/
      assets/
        foods/*.jpg
        drinks/*.jpg
      datastore.json
```

- 新增条目时会自动保存图片到对应目录  
- `datastore.json` 用于记录现有食物 / 饮料名称列表

---

## 🧩 依赖

本插件通过 `requirements.txt` 自动安装依赖：

- `Pillow`：用于图片处理（格式转换、缩放、去透明）

AstrBot 会自动根据 `requirements.txt` 安装所需依赖，无需手动操作。

---

## 📚 帮助文档

更多关于 AstrBot 的使用方法，可以参阅：

[帮助文档](https://astrbot.app)
