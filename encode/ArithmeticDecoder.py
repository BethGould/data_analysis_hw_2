import math
from encode.CountManagement import count_dynamic_k
from encode.ByteManagement import byte_mng_dec

# - keep track of and update l, h, bits
# {l_old, h_old, bits_old -> a, b -> h-l+1, h-l+1 / 2^n -> a+ term, b+ term -> l, 
#  h -> bin l, bin h -> enc update -> new bin l, new bin h, bits_new -> new l, new h}
class arith_code_dec_k:
    def __init__(self, counts_mngr:count_dynamic_k, byte_m:byte_mng_dec, whitespace:int, N = 40):
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
        self.whitespace = whitespace

        # counts
        self.count_m = counts_mngr
        self.k = counts_mngr.k
        self.first_choise = self.count_m.first_choise

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

        self.duration_static -= 8
        #print(self.duration_static)

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

    # saves our progress for the rare occasion when we need to roll back our reader
    def save_window(self):
        self.save_win = {
            'bits': self.bits,
            'win': self.window,
            'static': self.duration_static,
            'ii': self.byte_encode.ii,
            'jj': self.byte_encode.jj,
            'byte': self.byte_encode.byte,
            'cur_by': self.cur_by,
            'cur_bi': self.cur_bi,
            'end': self.end
        }

    def load_window(self):
        self.bits = self.save_win['bits']
        self.window = self.save_win['win']
        self.duration_static = self.save_win['static']
        self.byte_encode.ii = self.save_win['ii']
        self.byte_encode.jj = self.save_win['jj']
        self.byte_encode.byte = self.save_win['byte']
        self.cur_by = self.save_win['cur_by']
        self.cur_bi = self.save_win['cur_bi']
        self.end = self.save_win['end']

    # ----- here we have initialized everything,
    #      can check if we need to keep going
    #      and can find our byte string to read -----
            
    def remove_character(self):
        char = -1
        x = 0
        context = self.context
        excl = {}
        if self.first_choise:
            lib = self.count_m.get_counts_full(self.context, None)
            k_start = self.estimate_context_length(lib)
            context = context[k_start:]
            context_new = context
            if len(self.context) != len(lib) -1: print(len(context), len(lib))
            if len(context_new) != len(lib[k_start:])-1: print('lengths 2')
            for arr in lib[k_start:]:
                if arr is not None:
                    char = self.decode_character([arr[0], arr[1], excl])
                    excl = set(arr[0])
                context_new = context_new[1:]
                x = x + 1
                if char != -1:
                    break
        else:
            while char == -1 and x < len(self.context)+1:
                ret_arr = self.count_m.get_counts_full(context, excl = excl)
                char = self.decode_character(ret_arr[-1])
                context = context[len(ret_arr):]
                x = x + len(ret_arr)
                excl = set(ret_arr[-1][0])
            context = self.context

        if self.count_m.update_exclusion: self.char = self.count_m.increment_count_full(context, char, no_counts=x)
        else: self.char = self.count_m.increment_count_full(self.context, char)

        self.update_context() # so that the next context uses the current character and removes the oldest
        return self.char
    
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

    def decode_character(self, lib):
        # find the location in the probability space for our byte array window 
        hl1_N = float(self.ho-self.lo+1) / float(self.win_size)
        #w_pl = (self.window - self.lo) / hl1_N

        # find the probabilities of various characters
        lib = self.remove_masked(lib)
        char = -1
        if lib is not None and len(lib[0]) > 0:
            #a, char, b = self.find_window_chars(w_pl, lib)

            i = -1
            self.h = -1
            while self.l > self.window or self.h < self.window:
                i = i + 1
                if i < len(lib[0]): char = lib[0][i]
                else: char = -1
                counts = self.find_counts(lib[1], i)
                #print(counts)
                a,b = self.find_probs(counts)
                #hl1_N = float(self.ho-self.lo+1) / float(self.win_size)
                a_pl = math.ceil(hl1_N * a)
                b_pl = math.ceil(hl1_N * (b + 1)) - 1
                self.l = self.lo + a_pl
                self.h = self.lo + b_pl
                if i > len(lib[1]):
                    break

            # update l and h like before
            #a_pl = math.ceil(hl1_N * a)
            #b_pl = math.ceil(hl1_N * (b + 1)) - 1

            #self.l = self.lo + a_pl
            #self.h = self.lo + b_pl
            
            #self.save_window() # before I change anything
            enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
            self.new_lh(enc_n, bit_n) # removes bits from l and h

            # checks for border issues
            #if self.next_byte_outside_window():
            #    self.load_window()
            #    a,char,b = self.next_window_chars(a,char,b,lib)
                # then as before
            #    a_pl = math.ceil(hl1_N * a)
            #    b_pl = math.ceil(hl1_N * (b + 1)) - 1
            #    self.l = self.lo + a_pl
            #    self.h = self.lo + b_pl
            #    enc_n, bit_n = self.update_window() # shifts the window and records how many bits need to be removed from l and h
            #    self.new_lh(enc_n, bit_n) # removes bits from l and h

            # updates for the next run
            # there is definately an error here in the encoding ...
            self.char = char
            self.lo = self.ln
            self.ho = self.hn

        return char

    def remove_masked(self, lib):
        #print(lib)
        #print(len(lib[0]), len(lib[1]))
        alpha = lib[0].copy()
        counts = lib[1].copy()
        mask = lib[2].copy()
        for char in mask:
            i = alpha.index(char)
            alpha.pop(i)
            counts.pop(i)
            counts[-1] = counts[-1] - 1
        #print(alpha, counts)
        if 0 in counts:
            i = counts.index(0)
            #j = len(counts)
            alpha = alpha[:i]
            counts = counts[:i] + [counts[-1]]
            counts[-1] = len(alpha)
        #print(alpha, counts)
        if len(alpha) > 0: return [alpha, counts]
        else: return None

    def next_byte_outside_window(self):
        ret_val = False

        if self.window < self.ln:
            ret_val = True
        if self.window > self.hn:
            ret_val = True

        return ret_val

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
    
    def find_counts(self, counts, i):
        #print(counts)
        if len(counts) <= 1:
            return 0, 1, 0
        if i == 0:
            return [0, counts[0], sum(counts[1:])]
        if i >= len(counts)-1:
            i = len(counts) - 1
            return [sum(counts[:i]), counts[i], 0]
        return [sum(counts[:i]), counts[i], sum(counts[i+1:])]

    #      a, char, b = self.find_windows_chars(w_pl, ind1, ind2, char_arr)
    def find_window_chars(self, w_pl, lib):
        # empty = pass
        if lib == None or len(lib[0]) == 0:
            a = 0
            b = self.win_size - 1
            ret_char = -1
        else:
            chars = lib[0]
            counts = lib[1]

            if len(counts) != len(chars)+1: print(len(counts), len(chars))

            den = float(sum(counts))
            b_fl = float(0)
            a = lb = 0
            num = float(0)
            i = b = rb = -1
            while rb < math.ceil(w_pl):
                a = lb
                i += 1
                num = num + float(counts[i])
                b_fl = num / den
                rb = math.ceil(b_fl * self.win_size) - 1
                b = rb
                lb = rb + 1 # for the next cycle

            if i < len(chars):
                ret_char = chars[i]
            else:
                ret_char = -1
        
        return a, ret_char, b

    # move to the next character
    def next_window_chars(self, a, char, b, lib):
        chars = lib[0]
        counts = lib[1]

        a = b + 1
        i = chars.index(char) + 1

        den = float(sum(counts))
        num = float(sum(counts[:i+1]))
        b_fl = num / den

        b = math.ceil(b_fl * self.win_size) - 1

        if i < len(chars):
            ret_char = chars[i]
        else:
            ret_char = -1
        
        return a, ret_char, b

    # This loads the bits into the array and updates bits, but so far doesn't update l and h
    def update_window(self):
        l = self.l
        h = self.h

        nbitload = 0
        nbits = 0

        # both l and h are N bits long
        x = self.win_size

        lb = 0
        hb = 0
        
        for i in range(self.N):
            x = x // 2
            lb = l // x
            l = l % x
            hb = h // x
            h = h % x
            if lb == hb:
                self.shift_byte() # we are no longer loading
                while self.bits > 0:
                    self.bits -= 1
                nbitload += 1
            else:
                break

        # the final 0s in the file
        if nbitload == 0:
            self.static_count += 1
        else:
            self.static_count = 0

        # widening the window
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

        return nbitload,nbits

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
        if len(self.context) < self.k:
            self.context.append(self.char)
        else:
            self.context = self.context[1:] + [self.char]