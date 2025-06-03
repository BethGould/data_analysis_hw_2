#---------------------------------------------------------
# Helper Functions

# first = p1
# Encoding unchanged (not arithmetic)

from encode import byte_mng_dec

def find_k(text):
    ch =  [i for i in range(256)]

    byte_arr = []
    prob_arr = []

    for k in range(15):
        count = []

        for i in ch:
            search_bytes = bytes([ch[i]]+ byte_arr)
            count.append(text.count(search_bytes))

        byte_arr = [count.index(max(count))] + byte_arr
        prob_arr.append(max(count)/sum(count))

        #print(byte_arr)

        if max(count) < 20:
            #print(k)
            break
        if max(count)/sum(count) > 0.98:
            #print(k)
            break

    k = prob_arr.index(max(prob_arr))
    return k

def remove_byte_arr(bm:byte_mng_dec):
    sym_space = []
    bit_len = 8
    rem_chars = 256
    while rem_chars > 0:
        sym_space.append(bm.read_bits(bit_len))
        rem_chars = rem_chars - sym_space[-1]
        bit_len = len(bin(rem_chars - 1)) - 2
        #print(sym_space, rem_chars, bit_len)
        # 0 is possible as the first character, but not as a spacing
        # there also must be at least one character
        if sym_space[-1] == 0 and len(sym_space) > 1: 
            break
    
    if sym_space[-1] == 0 and len(sym_space) > 1:
        sym_space.pop() # remove the last, unused space, which ends the array
        
    #print(sym_space)

    #print(len(sym_space))
    for i in range(1,len(sym_space)):
        sym_space[i] = sym_space[i] + sym_space[i-1]

    #print(sym_space)

    sym = []
    for i in sym_space:
        sym.append(i)

    return sym


def remove_sym_arr(bm:byte_mng_dec):
    sym_space = []
    bit_len = int(7)
    rem_chars = int(128 - 26*2 - 10)
    while rem_chars > 0:
        sym_space.append(int(bm.read_bits(bit_len)))
        rem_chars = rem_chars - sym_space[-1]
        bit_len = len(bin(rem_chars - 1)) - 2
        # print(sym_space, rem_chars, bit_len)
        # 0 is possible as the first character, but not as a spacing
        # if there are no special chars, the last number will be >= 66; 
        # but 0 may be used instead as the end after this
        if sym_space[-1] == 0 and len(sym_space) > 1: 
            break
    
    sym_space.pop() # remove the last, unused space, which ends the array
    #print(sym_space)

    #print(len(sym_space))
    x1=x2=x3=False
    for i in range(1,len(sym_space)):
        sym_space[i] = sym_space[i] + sym_space[i-1]
        if sym_space[i] >= 48 and x1 == False: # digits
            x1 = True
            sym_space[i] += 10
        if sym_space[i] >= 65 and x2 == False: # uppercase letters
            x2 = True
            sym_space[i] += 26
        if sym_space[i] >= 97 and x3 == False: # lowercase layers
            x3 = True
            sym_space[i] += 26
    # now sym_space gives the ascii code for all the special characters

    #print(sym_space)

    sym = []
    for i in sym_space:
        sym.append(chr(i))

    return sym

def np2D_to_list1D(arr, mng_arr, m_ind = 0):
    out_arr = [arr[0]]
    max_ind = max(max(arr) + 1, m_ind) # so that giving this value is also allowed

    for i in range(1,len(arr)):
        # this is my exception, when the increase is not obvious
        # first condition -- that the old array increments, 
        # second condition, that the new index is greater than the previous, which won't increment the first normally
        if (mng_arr[i] != mng_arr[i-1]) and (arr[i] > arr[i-1]):
            out_arr.append(max_ind)
        out_arr.append(arr[i])

        # small bit of error-checking
        if (mng_arr[i] != mng_arr[i-1]) and (mng_arr[i] != (mng_arr[i-1] + 1)):
            print('error: ', i, ', ', mng_arr[i], ', ', mng_arr[i-1])

    return out_arr


