def split_choice_text(text):
    return [
        item.strip()
        for item in text.replace("，", ",").split(",")
        if item.strip()
    ]


def choose_many(label, options, prompt=None, empty_allowed=True):
    options = list(options)
    print(f"可选择的{label}如下：")
    for option in options:
        print(f"{option}, ", end="")

    prompt = prompt or f"请选择您想查询的{label}，多个值之间用逗号分隔："
    while True:
        values = split_choice_text(input(prompt))
        if not values:
            return None if empty_allowed else []
        values = list(dict.fromkeys(values))
        if set(values).issubset(set(options)):
            return values
        print(f"{label}超出可选范围")


def choose_one(label, options, prompt=None, empty_allowed=True):
    options = list(options)
    prompt = prompt or f"请输入{label}："
    while True:
        value = input(prompt).strip()
        if not value:
            return None if empty_allowed else ""
        if value in options:
            return value
        print(f"{label}不存在或超出可选范围")


def choose_dimension(options, prompt="请输入您想查询的维度："):
    while True:
        value = input(prompt).strip()
        if not value:
            return None
        if value in options:
            return value
        print("维度不合法")
