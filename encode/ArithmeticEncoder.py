import math
from encode.CountManagement import count_dynamic_k
from encode.ByteManagement import byte_mng_enc

# - keep track of and update l, h, bits
# {l_old, h_old, bits_old -> a, b -> h-l+1, h-l+1 / 2^n -> a+ term, b+ term -> l, 
#  h -> bin l, bin h -> enc update -> new bin l, new bin h, bits_new -> new l, new h}
class arith_code_enc_k:
    def __init__(self, counts_mngr:count_dynamic_k, N = 40):
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
        self.context = []
        self.char = 0

        # counts
        self.count_m = counts_mngr
        self.k = counts_mngr.k
        self.first_choise = self.count_m.first_choise

        # encoding
        self.byte_encode = byte_mng_enc()

        self.duration_static = 0

    # - find the probabilities and borders based on the counts (give counts, find left and right border)

    def find_probs(self, counts):
        den = float(counts[0]+counts[1]+counts[2])
        num1 = float(counts[0])
        num2 = float(counts[0]+counts[1])
        lb_fl = num1 / den
        rb_fl = num2 / den
        win = 2**self.N
        #print(lb_fl, rb_fl, win)
        lb = math.ceil(lb_fl * win)
        rb = math.ceil(rb_fl * win) - 1
        return lb, rb

    def add_character(self, char):
        self.char = char

        if self.first_choise:
            lib = self.count_m.get_counts_full(self.context, None)
            k_start = self.estimate_context_length(lib)
            context = self.context[k_start:]
            if self.count_m.update_exclusion: counts = self.count_m.get_counts_full(context, self.char)
            else: counts = self.count_m.get_counts_full(context, self.char, full_context=self.context)
            for i in counts:
                self.encode_character(i)
            #if not self.count_m.update_exclusion: self.count_m.increment_count_full(self.context, char)
        else:
            counts = self.count_m.get_counts_full(self.context, self.char)
            for i in counts:
                self.encode_character(i)

        self.update_context() # so that the next context uses the current character and removes the oldest

    # calculates maximum probability character in every step
    def estimate_context_length(self, lib):
        probs = [] #longest context to shortest context
        #print(lib)
        for i in lib:
            if i == None:
                probs.append(1)
            elif len(i[0])==0:
                probs.append(1)
            else:
                den = float(sum(i[1]))
                prob = [(float(x) / den) for x in i[1]]
                probs.append(max(prob))

        if len(probs) == 0: ret_val = 0
        else: ret_val = len(probs) - probs[::-1].index(max(probs)) - 1

        #print('return', ret_val)

        return ret_val # returns starting index in context array

    def estimate_context_length_v3(self, lib):
        probs = [] #longest context to shortest context
        #print(lib)
        for i in lib:
            if i == None:
                probs.append(0)
            elif len(i[0])==0:
                probs.append(0)
            else:
                den = float(sum(i[1]))
                prob = [(float(x) / den) for x in i[1]]
                #prob[-1] = 0
                probs.append(max(prob))

        if len(probs) == 0: ret_val = 0
        else: ret_val = len(probs) - probs[::-1].index(max(probs)) - 1

        #print('return', ret_val)

        return ret_val # returns starting index in context array

    # calculates full maximum probability character
    # currently only works for full counts    
    def estimate_context_length_v2(self, lib):
        #probs = [] #longest context to shortest context

        # find character
        if lib[-1] is not None:
            alpha = lib[-1][0].copy()
            count = lib[-1][1]
            alpha.append(-1)
            char = alpha[count.index(max(count))]
            del alpha
        else:
            char = -1

        #jj = -1

        # if the selected character is not in the library, 
        # then the selected character is considered to be new
        # or prob = 0
        # I need to test results for variants
        # always prob 0, always new, or new only for the first case. 
        probs = self.search_lib(lib, char, var=2)

        if len(probs) == 0: ret_val = 0
        else: ret_val = probs.index(max(probs))

        #print('return', ret_val)

        return ret_val # returns starting index in context array

    def search_lib(self, lib, char, var):
        probs = []
        jj = -2

        # if the selected character is not in the library, 
        # then the selected character is considered to be new
        # or prob = 0
        # I need to test results for variants
        # always prob 0, always new, or new only for the first case. 
        for j, i in enumerate(lib):
            # for list with only the new possibility
            if i == None or len(i[0])==0:
                if char == -1:
                    probs.append(1)
                else:
                    if var == 0:
                        probs.append(0)
                    elif var == 1:
                        probs.append(1)
                    else:
                        jj = j
                        p = 1
                        probs.append(0)
            # for lists with more characters
            else:
                den = float(sum(i[1]))
                prob = [(float(x) / den) for x in i[1]]
                # this is the new case
                if char == -1:
                    probs.append(prob[-1])
                elif char not in i[0]:
                    if var == 0:
                        probs.append(0)
                    elif var == 1:
                        probs.append(prob[-1])
                    else:
                        jj = j
                        p = prob[-1]
                        probs.append(0)
                else:
                    probs.append(prob[i[0].index(char)])

        if var != 0 and var != 1 and jj > -1:
            probs[jj] = p

        return probs


    def encode_character(self, counts):
        a,b = self.find_probs(counts)

        #print("ch: ", char, "a,b: ", format(a, '040b'), format(b, '040b'))
        

        hl1_N = float(self.ho-self.lo+1) / float(self.win_size)
        a_pl = math.ceil(hl1_N * a)
        b_pl = math.ceil(hl1_N * (b + 1)) - 1

        #print("num: ", float(self.ho-self.lo))
        #print(format(self.window, '040b'))


        self.l = self.lo + a_pl
        self.h = self.lo + b_pl

        #print("ch: ", char, "l,h:", format(self.l, '032b'), format(self.h, '032b'))


        #print("new l, h: ", float(self.h-self.l))
        enc_n, bit_n = self.encode1() # loads bits into the bit array and records how many bits need to be removed from l and h
        self.new_lh(enc_n, bit_n) # removes bits from l and h
        #print("remove: ", float(self.hn-self.ln), enc_n, bit_n)

        # updates for the next run
        self.lo = self.ln
        self.ho = self.hn

    # This appears to work properly.
    # This loads the bits into the array and updates bits, but so far doesn't update l and h
    def encode1(self):
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
                self.byte_encode.load_bits(lb, 1)
                while self.bits > 0:
                    self.byte_encode.load_bits(not(lb),1)
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
            else:
                break

        #print(self.h-self.l, nbitload, nbits)
        return nbitload,nbits

    # again, I need to check this and check the logic
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

    def update_context(self):
        if len(self.context) < self.k:
            self.context.append(self.char)
        else:
            self.context = self.context[1:] + [self.char]

    # I need error-checking here to prevent using any routines if this has already been applied
    def finalize(self):
        self.byte_encode.load_bits(1,1) # this is always 1, because 00, 01, 11 are the only possibilities, and 00 and 11 will already be removed.
        if self.duration_static > 0:
            self.byte_encode.load_bits(0, self.duration_static) # how many final characters the fraction was unchanged

        #print(self.duration_static)
            
        # now to finalize the bytestream
        a = 8 - self.byte_encode.bit_count
        # the encoding is already correct unless a = 8
        if a == 8:
            a = 0
            # remove the last zero byte
            b = self.byte_encode.byte_store.pop()
        return a