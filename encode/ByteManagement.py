
# - store bits and bytes, take bits and add it to the byte list (input array of bools, update encoding)
class byte_mng_enc:
    def __init__(self):
        self.byte_store = [0] # here I am filling the bytes, should be integers from 0 to 255
        self.bit_count = 0    # this is the number of bits in byte_store which are full; ensures that I don't overfill bytes and send them to the string when ready
        self.j = 0            # counts the length of byte_store
        
    def load_bits(self, bits, lngth):
        # the old bits are already shifted appropriately
        jj = self.byte_store[self.j]
        
        # bit shift new bits
        if self.bit_count < (8 - lngth): 
            ii = bits << (8 - lngth - self.bit_count)
        elif self.bit_count == (8 - lngth):
            ii = bits
        else:
            ii = bits >> (self.bit_count - 8 + lngth) # The excess will go off the end. I will encode them later.

        #print(lngth, self.bit_count, jj, ii)
        # bitwise or is the same as + in this case
        self.byte_store[self.j] = jj | ii
        used_bits = 8 - self.bit_count     # for when bit_count + lngth > 7
        self.bit_count += lngth

        bits_n = bits
        lngth_n = lngth

        #print(lngth, self.bit_count, jj, ii)
        # now, to work on the next byte
        while self.bit_count > 7:
            #print('here')
            self.j += 1
            self.bit_count -=8
            
            # we now need to take only the right most bit_count bits and put it in ii
            lngth_n -= used_bits
            bits_n = bits_n % (2**lngth_n) # removes the used bits
            if self.bit_count < 8:
                ii = (bits_n << 8 - lngth_n)%256
            else:
                ii = bits_n >> (lngth_n - 8)
                used_bits = 8
                
            self.byte_store.append(ii)

    # load letter and load word are for the abreviation list and name list
    def load_letter(self, cha):
        #000xx = stop
        #0010x = stop
        #0011x = ab
        #01xxx = c-j
        #10xxx = k-r
        #11xxx = s-z

        code_a = int('110', 2)
        num = ord(cha) - ord('a') + code_a # the order is unchanged, but the numbering starts earlier
        if num > 0 and num < 32:
            self.load_bits(num, 5)
        elif num <= 0:
            self.load_bits(0,3) # stop condition
        else:
            self.load_bits(2,4) # if I need another indicator

    # this will load the whole word into the bit string, then add a stop condition
    def load_word(self, word):
        word2 = word.lower()
        word2 = word2 + ' '
        for i in range(len(word2)):
            self.load_letter(word2[i])

    # now for the code for ternary code
    def load_ternary(self, num):
        # 00, 01, 10, 11
        # leading will be 1 or 0

        # number of digits for base 3 representation
        n = 0
        x = num
        while x >= 1:
            x = x / 3
            n += 1
        n2 = n

        # start with the leading bit
        # there are two variants only: 1 or 2
        n = n-1
        x = num // 3**n
        y = num % 3**n

        #print(x,y, x-1)
        self.load_bits(x-1,1) # 1 for 2 and 0 for 1
        
        # repeat for the rest of the digits
        for i in range(n2-1):
            n = n-1
            x = y // 3**n
            y = y % 3**n
            #print(x,y,1+x)
            self.load_bits(1+x,2) # 01 = 0, 10 = 1, 11 = 2

        # and load the end of number code
        self.load_bits(0,2)
            
    def save_bits(self, filename):
        self.byte_encode = bytearray(self.byte_store)
        with open(filename, "wb") as f:
            f.write(self.byte_encode)


# load the file, remove bits from the byte array
# byte_store = loaded encoded text
# byte = int from 0 to 255, which holds the current byte, with used bits set to 0
# jj = index of byte_store (our current byte)
# ii = current bit within our current byte, from 0 (all available) to 7 (only the last bit is available)
# ll = len(byte_store)
class byte_mng_dec:
    def __init__(self):
        self.byte_store = b'' # here I am filling the bytes, should be integers from 0 to 255
        self.byte = 0         # active byte

        self.ii = 0           # bits already read, goes from 0 to 7
        self.jj = 0           # bytes already read
        self.ll = 0           # length of the bytearray

        self.iio = 0
        self.jjo = 0
        self.rem = self.ll
        
    # unlike the previous version, the file is read first, not last
    # I need to check that this does what I think it does
    def load_file(self, filename):
        with open(filename, "rb") as f:
            self.byte_store = f.read() # the file should be put into a byte stream
            
        self.byte = self.byte_store[0]
        self.ii = 0         
        self.jj = 0          
        self.ll = len(self.byte_store) 

        self.iio = 0
        self.jjo = 0
        self.byteo = self.byte
        self.rem = self.ll
        
    # Once I open a file, I can start reading it. I never alter the data, but I will not access what has already been read. 
    # The first function assumes a known number of bits. We remove them one-by-one or 2 by 2 if we don't know how many we need.
    # sets self.iio and self.jjo, so the start of reading can be reset
    # return: value (int), whether or not we reach or superceed the length of the file
    def read_bits(self, lngth):
        done = False
        self.iio = self.ii
        self.jjo = self.jj
        self.byteo = self.byte
        self.rem = self.ll - self.jj
        
        # error-checking
        if self.ll == 0:
            print('File not defined.')
            done = True

        if self.rem == 0:
            print('End of file previously reached.')
            done = True

        ret_arr = [self.byte] # start with our return here
        used_bits = 8 - self.ii # used for length > remaining bit size
        k = (lngth - used_bits) // 8 # used for length > remaining bit size + 8

        #print("part1: ", self.ii, ", ", self.byte, ", ", lngth)
        
        # don't remove the bytes which don't need to be removed
        if (self.ii < (8 - lngth)) & (done == False): 
            mask = int(255) - int((2**(8 - lngth - self.ii) - 1))
            ret_arr[0] = ret_arr[0] & mask
            self.ii = self.ii + lngth
            mask = int(2**(8-self.ii) - 1)
            self.byte = self.byte & mask
            done = True

        #print("part1: ", self.ii, ", ", self.byte, ", ", lngth, ", ", done)

        #print(self.ii, self.jj)

        # full bytes
        if (done == False):
            if k > 0:
                for i in range(1, k+1):
                    if self.jj + i < self.ll:
                        ret_arr.append(self.byte_store[self.jj+i])
                    else:
                        print('Reached end of array.')
                        done = True
                        break
            if k >= 0:
                self.jj += k+1
                if self.jj < self.ll:
                    self.byte = self.byte_store[self.jj]
                else:
                    self.byte = 0 # end of array
                self.ii = 0 # return to beginning
                used_bits = used_bits + 8 * k
                
        if (done == False) & (lngth == used_bits):
            done = True
        elif (done == False) & (self.jj >= self.ll):
            print('Reached end of file')
            done = True
        elif (done == False) & (used_bits > lngth):
            print(lngth, used_bits)
            done = True

        #print(self.ii, self.jj)

        # and for the last byte
        if done == False:
            ret_arr.append(self.byte)
            #remaining bits
            rem_bits = lngth - used_bits
            #print("part2: ", rem_bits, ", ", lngth, ", ", used_bits)
            i = rem_bits
            mask = int(255) - int((2**(8-i) - 1))
            #if i > 8: print(i)
            ret_arr[-1] = ret_arr[-1] & mask
            self.ii = i
            mask = int((2**(8-i) - 1))
            self.byte = self.byte & mask

        #print(self.ii, self.jj, ret_arr)

        return self.byte_to_int(ret_arr, self.iio, self.ii)

    # this combines all bits into an integer
    def byte_to_int(self, byte_arr, start, end):
        lgt = len(byte_arr)
        num_bits = (lgt-1)*8 - start + end
        if end == 0:
            num_bits += 8
        out = 0
        for i in range(num_bits):
            # we want to take of the bit at index start + i
            ind = start + i
            kk = ind // 8
            ind = ind % 8
            pwr1 = int(2**(7-ind))
            num = pwr1 & byte_arr[kk] 
            #if ind < 7: num = num >> (7-ind)
            pwr_full = int(2**(num_bits - i - 1))
            if num > 0: out += pwr_full
        return(out)

    # if I read the next byte as a test, and find it is for the next section instead
    def revert(self):
        self.ii = self.iio
        self.jj = self.jjo
        self.byte = self.byteo
        self.rem = self.ll - self.jj
        
    def to_end_of_byte(self):
        if self.ii > 0:
            self.jj = self.jj + 1
        self.ii = 0
        self.rem = self.ll - self.jj
        if self.rem > 0:
            self.byte = self.byte_store[self.jj]
        else:
            self.byte = 0

    # now for the code for ternary code
    def read_ternary(self):
        # 00, 01, 10, 11
        # leading will be 1 or 0

        # 1 for 2 and 0 for 1
        # this gets the leading digit
        ter = [self.read_bits(1)+1]

        # repeat for the rest of the digits
        # 01 = 0, 10 = 1, 11 = 2
        code = 0
        while code >= 0:
            code = self.read_bits(2) - 1
            if code >= 0:
                ter.append(code)

        #print(ter, code)

        # now to return the number
        num = 0
        for i in range(len(ter)):
            #print(num)
            num += ter[i] * (3**(len(ter)-1-i))
            
        return num

    def read_list(self):
        word_arr = []
        cont = True
        while cont:
            word = self.read_word()
            if word == '':
                cont = False
            else:
                word_arr.append(word)
        return word_arr

    def read_word(self):
        word = ''
        cont = True
        while cont:
            char = self.read_char()
            if char == '':
                cont = False
            else:
                word = word + char
        return word

    def read_char(self):
        #000xx = stop
        #0010x = stop
        #0011x = ab
        #01xxx = c-j
        #10xxx = k-r
        #11xxx = s-z
        
        code_a = ord('a') - int('110', 2)
        #num = ord(cha) - ord('a') + code_a # the order is unchanged, but the numbering starts earlier
        #ord(cha) = num + ord('a') - code_a
        
        f3b = self.read_bits(3)
        if f3b == 0:
            char = ''
        elif f3b == 1:
            b4 = self.read_bits(1)
            if b4 == 0:
                char = '' # I could add a separate behavor here, but right now I have not.
            else:
                b5 = self.read_bits(1)
                if b5 == 0:
                    char = 'a'
                else:
                    char = 'b'
        else:
            b45 = self.read_bits(2)
            char_num = b45 + f3b*4 + code_a
            char = chr(char_num)

        return char