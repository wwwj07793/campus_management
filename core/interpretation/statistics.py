import numpy as np


def _to_numeric_array(values):
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    return np.array(numbers, dtype=float)


def numeric_statistics(values):
    numbers = _to_numeric_array(values)
    if numbers.size == 0:
        return {
            "count": 0,
            "max": None,
            "min": None,
            "average": None,
            "std": None,
            "var": None,
        }

    return {
        "count": int(numbers.size),
        "max": float(np.max(numbers)),
        "min": float(np.min(numbers)),
        "average": float(np.mean(numbers)),
        "std": float(np.std(numbers)),
        "var": float(np.var(numbers)),
    }


def score_statistics(scores):
    numbers = _to_numeric_array(scores)
    result = numeric_statistics(numbers)
    if numbers.size == 0:
        result.update({
            "pass_rate": None,
            "no_pass_rate": None,
            "excellent_rate": None,
        })
        return result

    result.update({
        "pass_rate": float(np.mean(numbers >= 60)),
        "no_pass_rate": float(np.mean(numbers < 60)),
        "excellent_rate": float(np.mean(numbers >= 85)),
    })
    return result


def gpa_statistics(gpas):
    numbers = _to_numeric_array(gpas)
    result = numeric_statistics(numbers)
    if numbers.size == 0:
        result.update({
            "pass_rate": None,
            "no_pass_rate": None,
            "excellent_rate": None,
        })
        return result

    result.update({
        "pass_rate": float(np.mean(numbers >= 2.0)),
        "no_pass_rate": float(np.mean(numbers < 2.0)),
        "excellent_rate": float(np.mean(numbers >= 3.5)),
    })
    return result


def format_score_statistics(stats):
    if stats["count"] == 0:
        return "暂无可统计的分数数据"
    return (
        f"最高分：{stats['max']}，最低分：{stats['min']}，"
        f"平均分：{stats['average']}，标准差：{stats['std']}，"
        f"方差：{stats['var']}，通过率：{stats['pass_rate']}，"
        f"挂科率：{stats['no_pass_rate']}，优秀率：{stats['excellent_rate']}"
    )


def format_gpa_statistics(stats):
    if stats["count"] == 0:
        return "暂无可统计的绩点数据"
    return (
        f"最高绩点：{stats['max']}，最低绩点：{stats['min']}，"
        f"平均绩点：{stats['average']}，标准差：{stats['std']}，"
        f"方差：{stats['var']}，达标率：{stats['pass_rate']}，"
        f"未达标率：{stats['no_pass_rate']}，优秀率：{stats['excellent_rate']}"
    )


def print_score_statistics(scores):
    stats = score_statistics(scores)
    print(format_score_statistics(stats))
    return stats


def print_gpa_statistics(gpas):
    stats = gpa_statistics(gpas)
    print(format_gpa_statistics(stats))
    return stats
