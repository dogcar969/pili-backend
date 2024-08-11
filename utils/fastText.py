# 看是否可以运行
import math

# import fasttext
# import thulac
# ft = fasttext.load_model('../fastText.bin')
# sentences = ['当你说出那句并无歧视的时候，你就已经在歧视了。因为你默认爱嚼舌根是女性的特点。','千万不要疲劳驾驶啊各位，千万！！前面过年开车从大连回黑龙江老家，开着开着就忽悠一下睡过去了…感觉睡了有几分钟，忽悠一下又醒了，赶紧下高速找地儿睡觉去了，吓尿了']
# thu = thulac.thulac(seg_only=True)
# def predict(sentence):
#     sentence = ' '.join([array[0] for array in thu.cut(sentence)])
#     print(sentence)
#     result = ft.predict(sentence)
#     score = 1-result[1][0] if result[0][0]=='__label__0' else result[1][0]
#     score = 0 if score<0 else score
#     score = 1 if score>1 else score
#     score = math.floor(score/0.2)
#     print(result)
#     return score
# for sentence in sentences:
#     print(predict(sentence))


# 能送到这一步的只有有审核屏蔽词的和没有屏蔽词的
safeWords = ['safe']
badWords = ['bad']
sentence = "safe word and bad word won't be counted"
frequency = {}

import thulac
thu = thulac.thulac(seg_only=True)
def seg(sentence):
    words = thu.cut(sentence,text=True)
    words = words.split(' ')
    for word in words:
        if word in safeWords:
            continue
        if word in frequency.keys():
            frequency[word]+=1
        else:
            frequency.update({word:1})

seg(sentence)
print(frequency)