import math
from encode import count_static_k, byte_mng_dec, count_mng

#import encode
# - keep track of and update l, h, bits
# {l_old, h_old, bits_old -> a, b -> h-l+1, h-l+1 / 2^n -> a+ term, b+ term -> l, 
#  h -> bin l, bin h -> enc update -> new bin l, new bin h, bits_new -> new l, new h}
class arith_code_mng_dec:
    def __init__(self, counts_mngr:count_mng, byte_m:byte_mng_dec):
        # window size
        self.N = 40
        self.win_size = 2**self.N

        # left and right borders
        # I know I don't need so many, but it should be fine right now
        self.l = 0
        self.h = self.win_size - 1
        self.bits = 0
        self.lo = 0
        self.ho = self.win_size - 1
        self.ln = 0
        self.hn = self.win_size - 1

        # counts
        self.find_counts = counts_mngr

        # encoding
        self.byte_encode = byte_m
        self.duration_static = 0
        self.static_count = 0
        self.end = 0
        self.window = 0

        self.byte_l = self.byte_encode.ll -  1
        self.cur_by = self.byte_encode.jj
        self.cur_bi = self.byte_encode.ii
        self.find_first_byte() # finds my window, removing it from the bit storage


    def read_bit(self):
        if (self.cur_by < self.byte_l):
            bit = self.byte_encode.read_bits(1)
            self.cur_by = self.byte_encode.jj
            self.cur_bi = self.byte_encode.ii                                                                
        else:
            bit = 0
            self.end = self.end + 1 # I don't think I need this, but ...
        return bit

    def find_first_byte(self):
        byte = 0
        for i in range(self.N):
            bit = self.read_bit()
            byte = byte << 1
            byte = byte | bit
        self.window = byte

    def shift_byte(self, n=1):
        for i in range(n):
            self.window = (self.window << 1) % self.win_size
            self.window = self.window | self.read_bit()

    def shift_byte_bits(self, n=1):
        for i in range(n):
            fb = (self.window // 2**(self.N-1)) << (self.N-1)
            self.window = (self.window << 1) % 2**(self.N-1) # removes 2 bits from the start, clearing a spot at the end and at the beginning
            self.window = self.window | self.read_bit() # add a bit to the end
            self.window = self.window | fb # return the first bit to the beginning

    # ----- here we have initialized everything,
    #      can check if we need to keep going
    #      and can find our byte string to read -----
            
    def remove_character(self):
        # find the location in the probability space for our byte array window 
        hl1_N = float(self.ho-self.lo+1) / float(self.win_size)
        w_pl = (self.window - self.lo) / hl1_N
        #print('w_pl, lo, ho, win')
        #print(bin(math.ceil(w_pl)), bin(self.lo), bin(self.ho), bin(self.window))

        # find the probabilities of various characters
        #char_arr = self.find_counts.alphabet.copy()
        a, char, b = self.find_window_chars(w_pl)

        # update l and h like before
        a_pl = math.ceil(hl1_N * a)
        b_pl = math.ceil(hl1_N * (b + 1)) - 1

        self.l = self.lo + a_pl
        self.h = self.lo + b_pl
        
        #print(format(self.l, '032b'),",", format(self.h, '032b'),",", format(self.window, '032b'))
        #print("new l, h: ", bin(self.h), bin(self.l))
        enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
        self.new_lh(enc_n, bit_n) # removes bits from l and h
        #print("remove: ", bin(self.hn), bin(self.ln), enc_n, bit_n)

        # updates for the next run
        # there is definately an error here in the encoding ...
        self.char = char
        self.lo = self.ln
        self.ho = self.hn
        #self.update_context() # so that the next context uses the current character and removes the oldest

        return char #ch[char] # this array should not be global ... 

    #      a, char, b = self.find_windows_chars(w_pl, ind1, ind2, char_arr)
    def find_window_chars(self, w_pl):
        # this gets the counts
        char_counts = self.find_counts.get_counts()
        #print(char_counts)
        if char_counts is None:
            a = 0
            b = self.win_size - 1
            i = 0
        else:
            den = float(sum(char_counts))
            b_fl = float(0)
            a = lb = 0
            num = float(0)
            i = b = rb = -1
            while rb < math.ceil(w_pl):
                a = lb
                i += 1
                num = num + float(char_counts[i])
                b_fl = num / den
                rb = math.ceil(b_fl * self.win_size) - 1
                b = rb
                lb = rb + 1 # for the next cycle
        
        ret_char = self.find_counts.increment_count(i)

        return a, ret_char, b


    #enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
    #self.new_lh(enc_n, bit_n) # removes bits from l and h
    # This is from the previous
    # This loads the bits into the array and updates bits, but so far doesn't update l and h
    def update_window(self):
        l = self.l
        h = self.h

        nbitload = 0
        nbits = 0

        #print(self.h-self.l)
        # both l and h are N bits long
        x = self.win_size
        #print(l / x, h / x)

        lb = 0
        hb = 0
        
        for i in range(self.N):
            #print("bits:", i, lb,hb, l/x, h/x)
            x = x // 2
            lb = l // x
            l = l % x
            hb = h // x
            h = h % x
            #print("bits:", i, lb,hb, l/x, h/x, self.bits)
            if lb == hb:
                self.shift_byte() # we are no longer loading
                while self.bits > 0:
                    #self.byte_encode.load_bits(1,1) # they are removed earlier
                    #self.shift_byte_bits()
                    self.bits -= 1
                nbitload += 1
            else:
                #print(i)
                break

        # the final 0s in the file
        if nbitload == 0:
            self.duration_static += 1
        else:
            self.duration_static = 0

        # widening the window
        # print(l / x, h / x)
        for i in range(self.N - nbitload - 1):
            x = x // 2
            lb = l // x
            l = l % x
            hb = h // x
            h = h % x
            if lb == 1 and hb == 0:
                nbits += 1
                self.bits += 1
                self.shift_byte_bits()
            else:
                break

        #print(self.h-self.l, nbitload, nbits)
        return nbitload,nbits

    # again, I need to check this and check the logic
    # should be unchanged
    def new_lh(self, nbitload, nbits):
        # removing bits
        self.ln = (self.l << nbitload) % self.win_size
        self.hn = (self.h << nbitload) % self.win_size
        self.hn = self.hn | (2**nbitload - 1) # fill the end with 1s, not 0s

        # widening of the window
        if nbits > 0:
            l_fb = (self.ln // 2**(self.N-1)) << (self.N-1)
            h_fb = (self.hn // 2**(self.N-1)) << (self.N-1)
            self.ln = (self.ln % 2**(self.N-1-nbits)) << nbits
            self.hn = (self.hn % 2**(self.N-1-nbits)) << nbits
            self.hn = self.hn | (2**nbits - 1) # fill the end with 1s, not 0s
            # and return the first bit to the array
            self.ln = self.ln | l_fb
            self.hn = self.hn | h_fb
    
    # This deals with the widening of the window removing needed bits from my byte stream 
    def end_stream(self):
        self.byte_encode.ii = self.byte_encode.ii - self.bits
        while self.byte_encode.ii < 0:
            self.byte_encode.jj -= 1
            self.byte_encode.ii += 8
        self.byte_encode.byte = self.byte_encode.byte_store[self.byte_encode.jj]
        self.byte_encode.byte = self.byte_encode.byte % 2**(8-self.byte_encode.ii)


# -----------------------------------------------------------------------


# - keep track of and update l, h, bits
# {l_old, h_old, bits_old -> a, b -> h-l+1, h-l+1 / 2^n -> a+ term, b+ term -> l, 
#  h -> bin l, bin h -> enc update -> new bin l, new bin h, bits_new -> new l, new h}
class arith_code_dec_k_fixed:
    def __init__(self, context, counts_mngr:count_static_k, byte_m:byte_mng_dec, whitespace:int, N = 40):
        # window size
        self.N = N
        self.win_size = 2**self.N

        # left and right borders
        # I know I don't need so many, but it should be fine right now
        self.l = 0
        self.h = self.win_size - 1
        self.bits = 0
        self.lo = 0
        self.ho = self.win_size - 1
        self.ln = 0
        self.hn = self.win_size - 1

        # context
        self.context = context
        self.char = 0
        self.whitespace = whitespace

        # counts
        self.count_m = counts_mngr

        # encoding
        self.byte_encode = byte_m
        self.duration_static = 0
        self.static_count = 0
        self.end = 0
        self.window = 0
        self.contin = True

        self.find_last_byte()
        self.find_first_byte()

    def find_last_byte(self):
        self.byte_l = self.byte_encode.ll
        self.cur_by = self.byte_encode.jj
        self.cur_bi = self.byte_encode.ii
        self.bit_end = 7

        # remove 0 bytes
        byte = 0
        while (byte == 0) and (self.byte_l >= self.cur_by):
            self.byte_l = self.byte_l - 1
            byte = self.byte_encode.byte_store[self.byte_l]
            self.duration_static = self.duration_static + 8

        # now for 0 bits
        i = 0
        while i < 8:
            i = i + 1 
            byte_new = (byte >> i) << i
            if byte_new != byte:
                break

        self.bit_end = 8 - i
            
        # we need to fix duration_static now
        # this gives the minimum duration
        #if self.duration_static > 8:
        #    self.duration_static -= self.bit_end
        self.duration_static += i - 1
        self.duration_static -= self.whitespace

        # the last bit is now guarenteed to be 1 (unless there are no more remaining 1s)
        # the following condition marks this situation
        if (self.cur_by > self.byte_l) or ((self.cur_by == self.byte_l) and (self.cur_bi > self.bit_end)):
            self.contin = False

    def read_bit(self):
        if (self.cur_by < self.byte_l) or ((self.cur_by == self.byte_l) and (self.cur_bi <= self.bit_end)):
            bit = self.byte_encode.read_bits(1)
            self.cur_by = self.byte_encode.jj
            self.cur_bi = self.byte_encode.ii                                                                
        else:
            bit = 0
            self.end = self.end + 1 # I don't think I need this, but ...
        return bit

    def find_first_byte(self):
        byte = 0
        for i in range(self.N):
            bit = self.read_bit()
            byte = byte << 1
            byte = byte | bit
        self.window = byte
        
    def cont(self):
        # the last non-zero byte has been removed
        # and we need the count of unchanged cycles, which I think I forgot to encode
        if ((self.window == 2**(self.N - 1)) or (self.window == 0)) and ((self.cur_by > self.byte_l) or ((self.cur_by == self.byte_l) and (self.cur_bi > self.bit_end))):
            if (self.static_count >= self.duration_static) or (self.window == 0):
                self.contin = False
                
        return self.contin

    def shift_byte(self, n=1):
        for i in range(n):
            self.window = (self.window << 1) % self.win_size
            self.window = self.window | self.read_bit()

    def shift_byte_bits(self, n=1):
        for i in range(n):
            fb = (self.window // 2**(self.N-1)) << (self.N-1)
            self.window = (self.window << 1) % 2**(self.N-1) # removes 2 bits from the start, clearing a spot at the end and at the beginning
            self.window = self.window | self.read_bit() # add a bit to the end
            self.window = self.window | fb # return the first bit to the beginning

    # ----- here we have initialized everything,
    #      can check if we need to keep going
    #      and can find our byte string to read -----
            
    def remove_character(self):
        # find the location in the probability space for our byte array window 
        hl1_N = float(self.ho-self.lo+1) / float(self.win_size)
        w_pl = (self.window - self.lo) / hl1_N
        #print('w_pl, lo, ho, win')
        #print(bin(math.ceil(w_pl)), bin(self.lo), bin(self.ho), bin(self.window))

        # find the probabilities of various characters
        ind1, ind2, char_arr = self.find_nonzero_chars(self.context)
        a, char, b = self.find_window_chars(w_pl, ind1, ind2, char_arr)

        # update l and h like before
        a_pl = math.ceil(hl1_N * a)
        b_pl = math.ceil(hl1_N * (b + 1)) - 1

        self.l = self.lo + a_pl
        self.h = self.lo + b_pl
        
        #print(format(self.l, '032b'),",", format(self.h, '032b'),",", format(self.window, '032b'))
        #print("new l, h: ", bin(self.h), bin(self.l))
        enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
        self.new_lh(enc_n, bit_n) # removes bits from l and h
        #print("remove: ", bin(self.hn), bin(self.ln), enc_n, bit_n)

        # updates for the next run
        # there is definately an error here in the encoding ...
        self.char = char
        self.lo = self.ln
        self.ho = self.hn
        self.update_context() # so that the next context uses the current character and removes the oldest

        return self.count_m.alphabet[char] # this array should not be global ... 

    def find_nonzero_chars(self, context):
        return self.count_m.get_counts(context)

    #      a, char, b = self.find_windows_chars(w_pl, ind1, ind2, char_arr)
    def find_window_chars(self, w_pl, ind1, ind2, char_arr):
        # this gets the counts
        char_counts = self.count_m.counts[ind1:ind2+1]

        den = float(sum(char_counts))
        b_fl = float(0)
        a = lb = 0
        num = float(0)
        i = b = rb = -1
        while rb < math.ceil(w_pl):
            a = lb
            i += 1
            num = num + float(char_counts[i])
            b_fl = num / den
            rb = math.ceil(b_fl * self.win_size) - 1
            b = rb
            lb = rb + 1 # for the next cycle
        
        return a, char_arr[i], b


    #enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
    #self.new_lh(enc_n, bit_n) # removes bits from l and h
    # This is from the previous
    # This loads the bits into the array and updates bits, but so far doesn't update l and h
    def update_window(self):
        l = self.l
        h = self.h

        nbitload = 0
        nbits = 0

        #print(self.h-self.l)
        # both l and h are N bits long
        x = self.win_size
        #print(l / x, h / x)

        lb = 0
        hb = 0
        
        for i in range(self.N):
            #print("bits:", i, lb,hb, l/x, h/x)
            x = x // 2
            lb = l // x
            l = l % x
            hb = h // x
            h = h % x
            #print("bits:", i, lb,hb, l/x, h/x, self.bits)
            if lb == hb:
                self.shift_byte() # we are no longer loading
                while self.bits > 0:
                    #self.byte_encode.load_bits(1,1) # they are removed earlier
                    #self.shift_byte_bits()
                    self.bits -= 1
                nbitload += 1
            else:
                #print(i)
                break

        # the final 0s in the file
        if nbitload == 0:
            self.duration_static += 1
        else:
            self.duration_static = 0

        # widening the window
        # print(l / x, h / x)
        for i in range(self.N - nbitload - 1):
            x = x // 2
            lb = l // x
            l = l % x
            hb = h // x
            h = h % x
            if lb == 1 and hb == 0:
                nbits += 1
                self.bits += 1
                self.shift_byte_bits()
            else:
                break

        #print(self.h-self.l, nbitload, nbits)
        return nbitload,nbits

    # again, I need to check this and check the logic
    # should be unchanged
    def new_lh(self, nbitload, nbits):
        # removing bits
        self.ln = (self.l << nbitload) % self.win_size
        self.hn = (self.h << nbitload) % self.win_size
        self.hn = self.hn | (2**nbitload - 1) # fill the end with 1s, not 0s

        # widening of the window
        if nbits > 0:
            l_fb = (self.ln // 2**(self.N-1)) << (self.N-1)
            h_fb = (self.hn // 2**(self.N-1)) << (self.N-1)
            self.ln = (self.ln % 2**(self.N-1-nbits)) << nbits
            self.hn = (self.hn % 2**(self.N-1-nbits)) << nbits
            self.hn = self.hn | (2**nbits - 1) # fill the end with 1s, not 0s
            # and return the first bit to the array
            self.ln = self.ln | l_fb
            self.hn = self.hn | h_fb

    # unchanged
    def update_context(self):
        # This is not the most effective version of fofo list structure, but
        # I have only 3 elements, and it is the easiest to work with. 
        # I could get only 2 updates having a number which record the start, but
        # then I need to tell everything to access the array based on this.
        self.context[0] = self.context[1]
        self.context[1] = self.context[2]
        self.context[2] = self.char

        #print(self.context)

    # I need error-checking here to prevent using any routines if this has already been applied
    #def finalize(self):
    #    self.byte_encode.load_bits(1,1) # this is always 1, because 00, 01, 11 are the only possibilities, and 00 and 11 will already be removed.
    #    if self.duration_static > 0:
    #        self.byte_encode.load_bits(0, self.duration_static) # how many final characters the fraction was unchanged
            
        # now to finalize the bytestream
    #    a = 8 - self.byte_encode.bit_count
        # the encoding is already correct unless a = 8
    #    if a == 8:
    #        a = 0
            # remove the last zero byte
    #        b = self.byte_encode.byte_store.pop()
    #    return a