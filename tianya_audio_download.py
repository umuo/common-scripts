"""
批量下载 天涯神贴 音频
"""
import requests
import tqdm
import os

DOWNLOAD_PATH = r"/root/download"

audio_list =  [{
    "name": "绝密人性天数",
    "time": "2024-11-15",
    "url": "http://aod.cos.tx.xmcdn.com/storages/4cc1-audiofreehighqps/BD/FB/GKwRIW4LDqpbA1LclAMwoLE0.mp3",
    "description": "历史的任何一个朝代，都有两套知识,一套是门内知识，一套是门外知识,皇帝和有钱人把门内知识留给自己和子孙学习,从不外露,他们把门外知识拿出来给众生学习,门内知识教的都是权谋,手段，人性,帝王术……而门外知识,教的都是让你如何成为一个更听话的羊"
}, {
    "name": "寒门再难出贵族",
    "time": "2024-11-8",
    "url": "http://aod.cos.tx.xmcdn.com/storages/de1f-audiofreehighqps/43/C0/GKwRIasLDqqkBEQaIQMwoLuN.mp3",
    "description": "寒门再难出贵族，本文是一名银行hr写的，他接待了一群到银行实习的学生，然后观察他们发生的一系列的故事。像小说，但比小说更精彩，像现实，但比我们了解的现实更残酷。"
}, {
    "name": "社会不教，精英不讲，坎儿还得自己过！",
    "time": "2024-11-10",
    "url": "http://aod.cos.tx.xmcdn.com/storages/8c37-audiofreehighqps/7E/17/GKwRIDoLDqz3DX-u3QMwoSyG.mp3",
    "description": "社会不教精英不讲,坎还得自己过,揭秘人才成长规律,e路狂飙写在最后的前沿。"
}, {
    "name": "鸦片战争隐藏的真相（付费独享）",
    "time": "2024-11-24",
    "url": "",
    "description": "解密鸦片战争背后的秘密"
}, {
    "name": "江湖潜规则",
    "time": "2024-01-01",
    "url": "http://aod.cos.tx.xmcdn.com/storages/06aa-audiofreehighqps/8D/57/GKwRIasLDqmTAUOangMwoJz7.mp3",
    "description": "声明：江湖虚构, 可借鉴, 不可生搬硬套。送礼法则：第一步：送水果, 就问他一句话, 我符合获奖条件吗。第二步：送烟酒, 说您费心了, 成不成都没事。第三步：送钱, 说下不为例, 这三步走了就差不多了。送礼对象：送礼的对象永远不超过五个, 超过五个就有垃圾流量了。"
}, {
    "name": "开悟其实很简单,人人都可以开悟",
    "time": "2024-01-01",
    "url": "http://aod.cos.tx.xmcdn.com/storages/c2b2-audiofreehighqps/9A/8E/GKwRIUELDqnPAi8CSwMwoKLa.mp3",
    "description": "开悟其实很简单,人人都可以轻轻松��开悟。心灵不孤独，如何开悟，开悟之后是个怎样的状态，我们为什么要追求开悟，这是每一个修行人士都渴望了解的问题，据说地球上开悟的人不到百万分之一。"
}, {
    "name": "请块所谓的\"开光\"玉，不如养活的灵宠（付费独享）",
    "time": "2024-11-11",
    "url": "",
    "description": "今天给大家分享长文《请块所谓的开光玉,不如养活的灵宠》该贴子被网友评为天涯十大神贴之一,原作，神奇的老贼头"
}, {
    "name": "你不是不努力，而是体质太差了（付费独享）",
    "time": "2024-11-08",
    "url": "",
    "description": "从学生时代到成人社会，我们成绩不好，赚钱不多，常常会被人轻描淡写的一句话给概括，是不是你不够努力啊?你为什么成不了别人家的孩子"
}, {
    "name": "大明帝国有了全世界—半以上的白银，最终还是垮了",
    "time": "2024-11-19",
    "url": "http://aod.cos.tx.xmcdn.com/storages/a99e-audiofreehighqps/2C/9D/GKwRINsLEU1cAM1VEQMxtetJ.mp3",
    "description": "大明帝国有了全世界—半以上的白银，最终还是垮了"
}, {
    "name": "如何将身体恢复到完美状态",
    "time": "2024-11-08",
    "url": "http://aod.cos.tx.xmcdn.com/storages/4488-audiofreehighqps/F0/8D/GKwRIRwLDqkzAGGdjwMwoJiA.mp3",
    "description": "如何将你的身体恢复到完美状态，我会从五点纠正你，从体态，饮食，护肤，作息，运动，锻造你的完美状态。"
}, {
    "name": "莲蓬鬼话：大家都说说小时候的很奇怪的记忆和遇到的很奇怪的东西",
    "time": "2024-11-08",
    "url": "http://aod.cos.tx.xmcdn.com/storages/3759-audiofreehighqps/F1/75/GKwRINsLDqupBwwBegMwoNV5.mp3",
    "description": "大家都说说小时候很奇怪的记忆"
}, {
    "name": "山医命相卜,五术杂谈（付费独享）",
    "time": "2024-11-10",
    "url": "",
    "description": "大家好,我姓邓,和很多同龄人一样叫建中,今年55了,以前做过很多工作，去沿海打过工，在沿海做过建材生意,但是我这个人的主要兴趣不在打工或做生意，而在命理玄学。"
}, {
    "name": "莲蓬鬼话：爷孙俩的中医故事——每个人都可以读懂的中医（付费独享）",
    "time": "2024-11-10",
    "url": "",
    "description": "每个人都可以读懂的中医，在一个小山村里住着一个老先生跟一个小徒弟，老先生不知道什么时候来到这个小村子，本来大家都不知道他会医术的，只是偶尔邻居的伤风感冒或者缠缠绵绵的慢性病，老先生总是建议他们采些草药"
}, {
    "name": "莲蓬鬼话：揭秘玄学各大预测术根源之真传一句话，假传万卷书！（付费独享）",
    "time": "2024-11-10",
    "url": "",
    "description": "揭秘玄学各大预测术根源之真传一句话，假传万卷书！说到玄学，首说四门，易经，奇门遁甲，太乙神数，大六壬，易经为群经之首，奇门遁甲讲时空变化，运用时空变化百战百胜!"
}, {
    "name": "赚未来十年的钱丨作者：海边的老王（2009年）",
    "time": "2024-11-10",
    "url": "http://aod.cos.tx.xmcdn.com/storages/c1ec-audiofreehighqps/4E/B9/GKwRINsLDqs5BvzZegMwoMim.mp3",
    "description": "纯理论操作,信不信随你!前言，最近我的睡眠不正常，导致头痛思维混乱，因此过来写写文字整理思路，但这里全部都是描述性的文字，信马由缰，没有任何的数据支持，信不信随你"
}, {
    "name": "识人术！从零开始学面相（付费独享）",
    "time": "2024-11-10",
    "url": "",
    "description": "行走江湖，谈婚论嫁，我们大家都不可避免地跟形形色色的人打交道，这些人有的是官员，有的是商人，有的是黑道人物，他们中有的会成为我们的朋友，有的会成为我们的合作伙伴，有的会成为我们的敌人。"
}, {
    "name": "高敏感人格的究极形态",
    "time": "2024-11-11",
    "url": "http://aod.cos.tx.xmcdn.com/storages/6d46-audiofreehighqps/CB/9A/GKwRIJELDqkqAFyvhAMwoJf4.mp3",
    "description": "洞察力是高敏人群独有的强大天赋, 但在未建立本自具足的内在系统和正确认之前,只会导致讨好型人格或过度感知危险,而特别缺乏安全感,但如果通过修炼开发了此天赋,高敏人不仅能控制自己的情绪,还能高度觉知他人情绪。"
}, {
    "name": "富人最大的财富，是穷人",
    "time": "2024-11-11",
    "url": "http://aod.cos.tx.xmcdn.com/storages/a73d-audiofreehighqps/A5/EF/GKwRIJELDqlAAIq3MQMwoJkq.mp3",
    "description": "富人最大的财富，不是豪车,豪宅，不是乱七八糟的文物,存款，富人最大的财富，是穷人  "
}, {
    "name": "严肃的问题：人类怎样才能不被动物吃掉？",
    "time": "2024-11-11",
    "url": "http://aod.cos.tx.xmcdn.com/storages/28e6-audiofreehighqps/7F/84/GKwRIaILDqkuAEJpzQMwoJgf.mp3",
    "description": "人类怎样才能不被动物吃掉,很多人童年都有这样的经历,小时候不听话,父母会搬出一些厉害的动物吓唬孩子,“大灰狼来了”、再不听话大老虎就来吃你了”,并且百试百灵"
}, {
    "name": "一位贪官写给儿子的信（付费独享）",
    "time": "2024-11-12",
    "url": "",
    "description": "年轻人，千万不要被学历、能力迷惑住了，有才有德、德才兼备，那都是鸟托邦式的梦想，有人的地方，就有江湖，机关单位人脉、资历永远大于能力和学历。"
}, {
    "name": "修行的秘密",
    "time": "2024-11-12",
    "url": "https://tianyamp3.tianyashentie.org/%E4%BF%AE%E8%A1%8C%E7%9A%84%E7%A7%98%E5%AF%86.MP3",
    "description": "人生就是一场修行，而修行有十万八千法门，在众多方法的选择中，众生反而越来越迷茫，不是你不认真、不是你不努力、只是你获得的方法距离本质太远"
}, {
    "name": "识人术《冰鉴》",
    "time": "2024-11-12",
    "url": "http://aod.cos.tx.xmcdn.com/storages/3196-audiofreehighqps/CF/F7/GKwRIasLDqmsAVEnMQMwoJ9X.mp3",
    "description": "不管您是做企业，还是走仕途，体制内。还是体制外，做销聘，i还是做服务，甚至包括相亲，只要您需要与人打交道，都一定要听一听这个视频"
}, {
    "name": "揭秘千古第一禁书《商君书》",
    "time": "2024-11-14",
    "url": "http://aod.cos.tx.xmcdn.com/storages/1f64-audiofreehighqps/E8/32/GKwRIW4LDqlKAIi2igMwoJmv.mp3",
    "description": "要了解几千年来,人们被奴役和苦难的根源,商君书这本书不得不提,在封建社会的历史中,商君书被列为天下第一禁书,严禁在民间流传,但在封建帝王手里,它是被反复研读的珍贵资料"
}, {
    "name": "我是一名精神病医生，讲一讲那些你到死都不知道的事（付费独享）",
    "time": "2024-11-14",
    "url": "",
    "description": "08年的时候,因为考研失败,我从一所二流的医科大学毕了业,本想从事神经内科方面的职业,但是因为工作岗位竞争太激烈,我又不是名牌大学,加上后台也不硬,所以没能够争取到热门的职业,后来我的一位学长,建议我去考取精神科医师资格证,说这个职业会有外快,就这样糊里糊涂地参与了一所医院,住院医生的5年培训计划,当上了一名实习的精神科医师"
}, {
    "name": "一个外贸商人眼中，真实的朝鲜（付费独享）",
    "time": "2024-11-14",
    "url": "",
    "description": "1990年前后，边境贸易蓬勃开展起来。中国的一些外贸公司在丹东筹备成立了分公司，其任务主要是开展对朝贸易。和朝鲜人做生意以后，中国商人可以经常出入朝鲜，接触到了��们的政府官员、商贸人员、军人、以及普通百姓。对这个国家从陌生到熟悉，亲历了各种各样的事情。"
}, {
    "name": "一口气，6个小时用大白话，看完金瓶梅，西门庆的成长史",
    "time": "2024-11-14",
    "url": "http://aod.cos.tx.xmcdn.com/storages/a98e-audiofreehighqps/D3/FE/GKwRIJELDqwECn99uQMwoPc1.mp3",
    "description": "金瓶梅产生于明王朝后期,其作者妙笔生花,从那个腐烂奢靡的时代,萃取出最华美烂熟的果实,大家都以为世上只有一个西门庆,岂不知在腐败的朝代,每个州县都有一个西门庆,所差的不过是没有他帅罢了"
}, {
    "name": "扒一扒教师这个职业，当老师真的好痛苦啊",
    "time": "2024-11-14",
    "url": "http://aod.cos.tx.xmcdn.com/storages/c7a3-audiofreehighqps/8C/B1/GKwRIUELDqleAOtYVQMwoJqP.mp3",
    "description": "首先声明，我不是来炫耀的，也不是来贬低。写此贴的目的是为了让更多的人了解教师这个职业，让那些整天嚷着教师工作有多清闲，赚的有N多的人知道，当老师真的很不容易，没有那么多钱,更没有那么多的假期，工作也不是大家想象的那样，每天只需要上两节课，其他时间都呆着，还有寒暑假这样的悠闲。"
}, {
    "name": "养生的正确观念，调养脾胃就是补益气血（付费独享）",
    "time": "2024-11-14",
    "url": "",
    "description": "补益气血的根本是调养脾胃,调养脾胃的根本是饮食,可是现在很多所谓的专家说的最多的,不是如何养护脾胃,如何好好吃饭,而是天天在讲虚喝补,补血,补气补肾补心,总之只要说到养生就是一个字,补"
}, {
    "name": "我在淘宝给算命先生当客服的真实经历",
    "time": "2024-11-16",
    "url": "http://aod.cos.tx.xmcdn.com/storages/0be5-audiofreehighqps/F9/94/GKwRIRwLDoHiAS33BwMwlnxt.mp3",
    "description": "这么多年,我一直想写写自己的这些狗血人生经历,可是一直懒,今天无所事事下,终于开篇了,我现在在淘宝的一家算命店铺打工,给先生做客服,这是10年前我做梦都想不到的事情"
}, {
    "name": "记录倒闭公司老总回归市井生活",
    "time": "2024-11-19",
    "url": "http://aod.cos.tx.xmcdn.com/storages/978a-audiofreehighqps/58/66/GKwRIaILEVcCAZT6dQMxtnLh.mp3",
    "description": "记录倒闭公司老总回归市井生活"
}, {
    "name": "一定要学会自带财气",
    "time": "2024-11-19",
    "url": "http://aod.cos.tx.xmcdn.com/storages/3369-audiofreehighqps/37/68/GKwRIJELEVYQAJBFOwMxtmSE.mp3",
    "description": "一定要学会自带财气"
}, {
    "name": "公务员自身谈一谈体制内外��入差异（付费独享）",
    "time": "2024-11-19",
    "url": "",
    "description": "最近看到很多关于体制内外,收入待遇差异的文章,以及打架对体制内外的误解,因此以自身家庭为例,介绍一下本人的真实情况,并可以和网友真诚探讨一些体制内外的问题"
}, {
    "name": "拨开迷雾看未来",
    "time": "2024-11-19",
    "url": "http://aod.cos.tx.xmcdn.com/storages/ea93-audiofreehighqps/FA/DC/GKwRIJILEUpjAqwXhAMxtZR2.mp3",
    "description": "人类社会在短短的200多年时间里,完成了从机械化到电子化,网络化到智能化的发展阶段,我们这代人也经历了从收音机到电视,机到电脑到互联网到移动通讯等,在短短的几十年里,见证了从政治,经济文化到科技的种种革命性突破和飞速发展"
}, {
    "name": "送礼绝学108招",
    "time": "2024-11-19",
    "url": "http://aod.cos.tx.xmcdn.com/storages/c226-audiofreehighqps/80/67/GKwRIUELEUhjB4H-YAMxtVkM.mp3",
    "description": "必须学送礼,必须研究人际关系,必须是边学边用边用边学,里面的乾坤有多大呀,用了上瘾呀,有些事走正常程序永远都走不动,月收入的10%用来送礼,绝对比用月收入的10%购买理财产品赚钱"
}, {
    "name": "从海龟到公务员，说说在上��的艰难生活",
    "time": "2024-11-24",
    "url": "http://aod.cos.tx.xmcdn.com/storages/046a-audiofreehighqps/E9/8F/GKwRIJELF-pNApLPrgM0lAvo.mp3",
    "description": "本人1984年生人,中部地区省会城市出生,父母都是正儿八经的事业单位,朝九晚五,高中,我以高出省重点线30分的成绩,考入省重点一中大学,考入隔壁省重点大学电气工程系,2006年,以全额奖学金的身份,被亚洲排名前三的大学经管系录取,出国读研,2008年毕业回国"
}, {
    "name": "一个潜水多年的体制内的生意人来实际谈谈老百姓该怎么办（付费独享）",
    "time": "2024-11-24",
    "url": "",
    "description": "这篇文章2013年,也就是10年前在天涯论坛里受关注度非常高,元气的思想虽然很超前,文中很多思路即便放到10年后的今天,也依然很受用"
}, {
    "name": "惊天骗局，一位高级招商主管的自白",
    "time": "2024-11-24",
    "url": "http://aod.cos.tx.xmcdn.com/storages/45bb-audiofreehighqps/40/D3/GKwRIW4LF-z2AX_SIQM0lF3f.mp3",
    "description": "今天分享的这个文章,讲述的是一个刚毕业的大学生,在北京因金钱的诱惑,误入了一家皮包公司,表面上是一家国际知名服装品牌,诚邀全国各地加盟商合作,实则是一家骗子公司"
}, {
    "name": "一个十年检察官所经历的无数奇葩案件",
    "time": "2024-11-24",
    "url": "http://aod.cos.tx.xmcdn.com/storages/caf4-audiofreehighqps/B2/AA/GKwRIasLF_AeATxXBwM0lK2t.mp3",
    "description": "第一个故事,夜幕下的诱惑,一天早晨,一个年轻的小帅哥匆匆忙忙的到派出所报警,称他被一个女孩骗了很多钱,女孩的嫁在我们辖区,小帅哥是外地人,特意一路又跟过来到我们这报警"
}, {
    "name": "至所有兄弟，若是老婆出轨了，就一定要离婚",
    "time": "2024-11-24",
    "url": "http://aod.cos.tx.xmcdn.com/storages/a196-audiofreehighqps/7A/14/GKwRINsLGJNJAUgpJgM00LqK.mp3",
    "description": "我也成了这天涯里的绿帽男,一个只是新增了一个,看了3年多的天涯,我也把我的故事呈现出来,文笔不好,想到哪儿写到哪儿了"
}, {
    "name": "扫黄这么严，咱不聊大保健，就聊聊妓女那些事（付费独享）",
    "time": "2024-11-24",
    "url": "",
    "description": "最早的妓女诞生于何处，据专家们说,那时那地我们认为的肮脏和神圣,居然是混为一谈的,经宗教这个终极传销组织一番洗脑之后,对神充满了坚定的献身精神,他们来到神庙,当着神的面与认识不认识的男子做一番交易,并将购合所得的钱上交给神庙作为运营费用,以此完成对神的供奉"
}, {
    "name": "美院求学，我和同学在北京\"天上人间\"的日子（付费独享）",
    "time": "2024-11-24",
    "url": "",
    "description": "今天给大家分享一篇当年轰动天涯论坛的神贴,美院求学,我和同学在北京天上人间的日子,本文讲述了作者在京城最高级的会所天上人间,做小姐时的所见所欲的真实经历"
}]

def download_audio(audio):
    if audio["url"]:  # 检查 URL 是否不为空
        response = requests.get(audio["url"], stream=True)
        file_name = f"{audio['name']}.mp3"
        file_path = os.path.join(DOWNLOAD_PATH, file_name)

        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, 'wb') as file, tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as bar:
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                bar.update(len(data))

# 下载所有音频
for audio in audio_list:
    download_audio(audio)

