PC_corp = """
I Don’t Want To Go 
A Groovy Kind Of Love 
You Can’t Hurry Love 
This Must Be Love 
Take Me With You 
"""

AS_corp = """
All Out Of Love 
Here I Am 
I Remember Love 
Love Is All 
Don’t Tell Me 
"""

PC = ''.join(PC_corp.split('\n')).split(' ')
AS = ''.join(AS_corp.split('\n')).split(' ')


unique_words = {}

for word in PC:
    print(word)
    if word not in unique_words:
        unique_words[word] = [2, 1]
    else:
        unique_words[word][0] += 1

for word in AS:
    if word not in unique_words:
        unique_words[word] = [1, 2]
    else:
        unique_words[word][1] += 1


for key, value in unique_words:
