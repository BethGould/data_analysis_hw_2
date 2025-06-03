import numpy as np
import string
from encode import (count_mng_dyn_sta, byte_mng_enc, arith_code_mng_enc, 
                    count_mng_dynamic_old, np2D_to_list1D, arith_code_mng_dec, 
                    remove_sym_arr, byte_mng_dec)

def find_counts_text_enc(text, ch):
    # k = 0
    count1=np.zeros((61), int)
    for i in range(61):
        count1[i] = text.count(ch[i])
    c1_non0 = np.nonzero(count1)

    # k = 1
    str2 = '00'
    count2=np.zeros((61,61), int)
    for i in range(61):
        for j in range(61):
            str2 = ch[i]+ch[j]
            count2[i,j] = text.count(str2)
    num2_non0 = np.count_nonzero(count2)
    c2_non0 = np.nonzero(count2)

    # k = 2
    ii = jj = 0
    str3 = '000'
    count3n = np.zeros((num2_non0, len(ch)), int)
    for i in range(num2_non0):
        ii=c2_non0[0][i]
        jj=c2_non0[1][i]
        for j in range(len(ch)):
            str3 = ch[ii]+ch[jj]+ch[j]
            count3n[i,j] = text.count(str3)
    c3n_non0 = np.nonzero(count3n)

    # k = 2 full version
    count3 = np.zeros((61,61,61), int)
    str3 = '000'
    for i in range(61):
        for j in range(61):
            for k in range(61):
                str3 = ch[i]+ch[j]+ch[k]
                count3[i,j,k] = text.count(str3)      
    num_non0 = np.count_nonzero(count3) # much smaller -- 94.4% of cases don't exist
    c3_non0 = np.nonzero(count3)

    # k = 3
    ii = jj = kk = 0
    str4 = '0000'
    count4 = np.zeros((num_non0, len(ch)), int)
    for i in range(num_non0):
        ii=c3_non0[0][i]
        jj=c3_non0[1][i]
        kk=c3_non0[2][i]
        for j in range(len(ch)):
            str4 = ch[ii]+ch[jj]+ch[kk]+ch[j]
            count4[i,j] = text.count(str4)
    num4_non0 = np.count_nonzero(count4)
    c4_non0 = np.nonzero(count4)

    c4_arr = [0]*num4_non0
    for i in range(num4_non0):
        c4_arr[i] = count4[c4_non0[0][i], c4_non0[1][i]]

    return c1_non0, c2_non0, c3_non0, c3n_non0, c4_non0, count4, c4_arr

def encode_counts_text(text, counts_enc: byte_mng_enc, ch, c2_non0, c3n_non0, c4_non0, c4_arr):

    # p1
    # 0 means ending the array
    sim_arr = [10, 22, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 2, 5, 1, 0]
    # - size: (bit size -> 7, 6, 6, 6, {5}, 5, ..., 5, {4}, 4, 4, 4, 4, {2}, 2 or just all 7)
    # should be calculated automatically:  calc_sim_size(sim)
    size_sim_arr = [7, 6, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 2, 2]

    for i in range(len(sim_arr)):
        counts_enc.load_bits(sim_arr[i], size_sim_arr[i])

    # set up the alphabet
    array_nums = [i for i in range(len(ch)+1)]
    counts_dynamic_static = count_mng_dyn_sta(alphabet_in=array_nums)
    enc_mng_ds = arith_code_mng_enc(counts_mngr=counts_dynamic_static, bits_store=counts_enc)

    #p2
    f3_num = [ch.index(text[0]), ch.index(text[1]), ch.index(text[2])]
    for i in f3_num:
        enc_mng_ds.add_character(i)

    #p3
    p3_arr = np2D_to_list1D(c2_non0[1][:], c2_non0[0][:], 61)
    for i in p3_arr:
        enc_mng_ds.add_character(i)
    enc_mng_ds.add_character(61)

    #p4
    p4_arr = np2D_to_list1D(c3n_non0[1][:], c3n_non0[0][:], 61)
    for i in p4_arr:
        enc_mng_ds.add_character(i)
    enc_mng_ds.add_character(61)

    #p5
    p5_arr = np2D_to_list1D(c4_non0[1][:], c4_non0[0][:], 61)
    for i in p5_arr:
        enc_mng_ds.add_character(i)
    enc_mng_ds.add_character(61)

    # end of first arithmetic encoding
    enc_mng_ds.partial_finalize()

    counts_dynamic = count_mng_dynamic_old()
    enc_mng_d = arith_code_mng_enc(counts_mngr=counts_dynamic, bits_store=counts_enc)

    for i in c4_arr:
        enc_mng_d.add_character(i)

    enc_mng_d.partial_finalize()

    for i in range(len(counts_dynamic.alphabet)):
        counts_enc.load_ternary(counts_dynamic.alphabet[i])

def decode_counts_text(byte_count: byte_mng_dec):
    sim = remove_sym_arr(byte_count)
    n = len(sim) + 26 + 10
    size = len(bin(n)) - 2

    low = []
    for i in range(26):
        low.append(string.ascii_lowercase[i])
    num = []
    for i in range(10):
        num.append(string.digits[i])


    ch = []
    for i in range(48):
        if chr(i) in sim:    
            ch.append(chr(i))
    ch = ch + num
    for i in range(58, 97):
        if chr(i) in sim:    
            ch.append(chr(i))
    ch = ch + low
    for i in range(123, 128):
        if chr(i) in sim:
            ch.append(chr(i))

    # set up the alphabet
    array_nums = [i for i in range(len(ch)+1)]
    counts_dynamic_static = count_mng_dyn_sta(alphabet_in=array_nums)
    decode_dyn_st = arith_code_mng_dec(counts_mngr=counts_dynamic_static, byte_m=byte_count)

    # p2: {'ABC'} -- The first three characters of the document (index 0 - 60). 
    context = [] 
    #size = 6
    for i in range(3):
        context.append(decode_dyn_st.remove_character())

    # p3: {c2_non0\[1\]\[0\]+1, c2_non0\[1\]\[1:\]- c2_non0\[1\]\[0:-1\]} 
    # two indicies, first of length 61, second of leng
    # there should be 1427 numbers loaded, each with a length of 6 bits

    p3_arr = ([], [])
    notdone = True
    i = 0 # i is increasing by one at the beginning -- this gives the correct results
    j = 0
    notFirst= False

    while notdone:
        jo = j
        j = decode_dyn_st.remove_character()
        if j <= jo and notFirst:
            i = i + 1
            if i >= len(ch):
                print('i greater than len')
                #byte_count.revert()
                notdone = False
        elif j >= len(ch):
            i = i + 1
            if i < len(ch):
                j = decode_dyn_st.remove_character()
            else:
                notdone = False
        if notdone:
            p3_arr[0].append(i)
            p3_arr[1].append(j)
        notFirst = True

    # p4: {c3n_non0\[1\]\[0\]+1, c3n_non0\[1\]\[1:\]- c3n_non0\[1\]\[0:-1\]} -- Add 61 to all non-positive.
    # y = 61
    # target size -- 12699

    p4_arr = ([], [])
    notdone = True
    i = 0
    j = 0
    notFirst= False

    while notdone:
        jo = j
        j = decode_dyn_st.remove_character()
        if j <= jo and notFirst:
            i = i + 1
            if i >= len(p3_arr[0]):
                print('i greater than len')
                #byte_count.revert()
                notdone = False
        elif j >= len(ch):
            i = i + 1
            if i < len(p3_arr[0]):
                j = decode_dyn_st.remove_character()
            else:
                notdone = False
        if notdone:
            p4_arr[0].append(i)
            p4_arr[1].append(j)
        notFirst= True

    #  p5: {c4_non0\[1\]\[0\]+1, c4_non0\[1\]\[1:\]- c4_non0\[1\]\[0:-1\]} -- Add 61 to all non-positive character spacings. Counts are only important here, as the old counts can be calculated from these counts and the first 3 characters.
    # z = 61, to indicate end of file 
    # target size: 59088

    p5_arr = ([], [])
    notdone = True
    i = 0
    j = 0
    notFirst= False

    while notdone:
        jo = j
        j = decode_dyn_st.remove_character()
        if j <= jo and notFirst:
            i = i + 1
            if i >= len(p4_arr[0]):
                print('i greater than len')
                #byte_count.revert()
                notdone = False
        elif j >= len(ch):
            i = i + 1
            if i < len(p4_arr[0]):
                j = decode_dyn_st.remove_character()
            else:
                notdone = False
        if notdone:
            p5_arr[0].append(i)
            p5_arr[1].append(j)
        notFirst= True

    decode_dyn_st.end_stream()

    # set up the alphabet
    # we have a new count management, but the same byte management
    counts_dynamic = count_mng_dynamic_old()
    decode_dyn = arith_code_mng_dec(counts_mngr=counts_dynamic, byte_m=byte_count)

    count4 = [] #np.zeros(len(p5_arr[0]), 'int')

    # count4
    for i in range(len(p5_arr[0])):
        count4.append(decode_dyn.remove_character())

    #whitespace2 = byte_count.read_bits(3) # this exists only in the full file encod
    #byte_count.to_end_of_byte() # should be the end now, but needed if the files are joined

    decode_dyn.end_stream()

    tar_len = len(counts_dynamic.alphabet)

    count_alphabet = []
    for i in range(tar_len):
        count_alphabet.append(byte_count.read_ternary())

    for i in range(len(count4)):
        count4[i] = count_alphabet[count4[i]]

    return ch, context, p3_arr, p4_arr, p5_arr, count4