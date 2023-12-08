from marko import inline, Markdown
from marko.helpers import MarkoExtension


class Underline(inline.InlineElement):
    pattern = r"\(ins\)(.+)\(ins\)"
    parse_children = True

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


class Spoiler(inline.InlineElement):
    pattern = r"\(spl\)(.+)\(spl\)"
    parse_children = True

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


class Emoji(inline.InlineElement):
    pattern = r":(.+):"
    parse_children = False

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


class CustomEmoji(inline.InlineElement):
    pattern = r"\(emj\)(.+)\(emj\)\[([^\]]+)\]"
    parse_children = False

    def __init__(self, match):
        super().__init__(match)
        self.name = match.group(1)
        self.id = match.group(2)


class MentionChannel(inline.InlineElement):
    pattern = r"\(chn\)(\d+)\(chn\)"
    parse_children = False

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


class MentionUser(inline.InlineElement):
    pattern = r"\(met\)(\d+|here|all)\(met\)"
    parse_children = False

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


class MentionRole(inline.InlineElement):
    pattern = r"\(rol\)(\d+)\(rol\)"
    parse_children = False

    def __init__(self, match):
        super().__init__(match)
        self.target = match.group(1)


Ext = MarkoExtension(
    elements=[
        Underline,
        Spoiler,
        Emoji,
        CustomEmoji,
        MentionChannel,
        MentionUser,
        MentionRole,
    ]
)

kmd = Markdown(extensions=[Ext])

if __name__ == "__main__":
    res = kmd.parse(
        """
**官匹冲分挑战赛**
---
欢迎大家参与一月份举办的官匹冲分挑战赛。
本次挑战赛举办的目的是为了增加小伙伴们(chn)12345(chn)之间的默契程度，希望大家能在此次活动中结交更多的朋友。
**活动开始时间**
`2021年1月1日至2021年1月30日`(emj)smile(emj)[123]
**活动规则**
此次活动仅限(ins)**AK**(ins)及以下段位的小伙伴们参与，请大家保持绿色游戏原则，不要使用~~第三方辅助工具~~或~~炸鱼~~影响其他游戏玩家体验。
挑战赛奖励将根据账号累计上升段位发放奖励。:smile:
**活动奖励**
- 第一名：(spl)游戏加速器年卡(spl)
- 第二名：(spl)游戏加速器季卡(spl)
- 第三名：(spl)游戏加速器月卡(spl)
- 参与奖：(spl)所有参与活动的小伙伴都将获得(met)12345(met)一个服务器角色(spl)
        """.strip()
    )

    print(res)
