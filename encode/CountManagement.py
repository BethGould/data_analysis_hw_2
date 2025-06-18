# I need to test that switching this into the code leaves everything unchanged

# class count_mng_static(alphabet_in, counts_in)
# class count_static_k(k, alphabet_in, counts_in, count_indexes)
# class count_mng_dyn_sta(alphabet_in)
# class count_mng_dynamic(new_mode)
# class count_dynamic_k(k, new_mode)

class count_mng:
    def __init__(self):
        pass

    def get_counts(self, char=None):
        pass

    # this will need to return the corresponding index in the alphabet for the number
    # in the case of mode == 2, I need to return len(alphabet) for char not in alphabet
    def find_num_char(self, char):
        return self.alphabet.index(char)

class count_mng_static(count_mng):
    def __init__(self, alphabet_in, counts_in):
        self.alphabet = alphabet_in
        self.counts = counts_in
        self.k = 0
        self.mode = 0

    # The simplist variant. Known character means encoding, unknown for decoding.
    def get_counts(self, char = None):
        if char == None:
            return self.counts.copy()
        else:
            num_char = self.find_num_char(char)
            return [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])]

class count_static_k(count_mng_static):
    def __init__(self, k: int, alphabet_in, counts_in, count_indexes):
        count_mng_static.__init__(self, alphabet_in, counts_in)
        self.k = k
        self.mode = 3
        self.load_counts(k, count_indexes)

    def load_counts(self, k, count_indexes):
        # error check count_indexes based on size of k
        if k > 0:
            self.counts_index_old = []
            self.counts_index_new = []
            for i in range(k):
                self.counts_index_old.append(count_indexes[i][0])
                self.counts_index_new.append(count_indexes[i][1])

    def load_counts_2(self):
        self.children = []
        for i in self.alphabet:
            ind1 = self.counts_index_old[0].index(i)
            if i != self.alphabet[-1]: ind2 = self.counts_index_old[0].index(i+1)
            else: ind2 = len(self.counts_index_old[0])

            alph_new = self.counts_index_new[0][ind1:ind2]

            context_new = []

            for j in range(1, self.k):
                ind3 = self.counts_index_old[j].index(ind1)
                if ind2 < len(self.counts_index_old[j-1]): ind4 = self.counts_index_old[j].index(ind2)
                else: ind4 = len(self.counts_index_old[j])
                ind1 = ind3
                ind2 = ind4
                context_new.append([self.counts_index_old[j][ind1:ind2], self.counts_index_new[j][ind1:ind2]])

            count_new = self.counts[ind1:ind2]

            if self.k > 1:
                new_child = count_static_k(self.k-1, alph_new, count_new, context_new)
                new_child.load_counts_2(self)
            else:
                new_child = count_mng_static(alph_new, count_new, context_new)
            self.children.append(new_child)

    def get_counts_2(self, context, char=None, context_as_indicies=True):
        if context_as_indicies:
            for i in range(len(context)):
                context[i] = self.find_num_char(context[i])
        if self.k > 1: return self.children[context[0]].get_counts_2(context[1:], char, False)
        else: return self.children[context[0]].get_counts(char, False)

    def get_counts(self, context, char=None):
        ind1 = self.counts_index_old[0].index(context[0])
        ind2 = ind1

        #print(context, ind1, ind2)

        if char == None: char_arr = []
        for i in range(self.k-1):
            ind2 = self.counts_index_new[i].index(context[i+1],ind1)

            #print(context, i, ind1, ind2, self.counts_index_old[i][ind2], self.counts_index_new[i][ind2])

            if self.counts_index_old[i][ind2] != self.counts_index_old[i][ind1]:
                print('find_index issue, ', self.counts_index_old[i][ind2], ", ", ind2)
            ind1 = self.counts_index_old[i+1].index(ind2)

        if ind2 < len(self.counts_index_old[self.k-2])-1:
            ind3 = self.counts_index_old[self.k-1].index(ind2+1, ind1)
        else:
            ind3 = len(self.counts_index_new[self.k-1])

        #print(ind1, ind3, self.counts_index_old[-1][ind1], self.counts_index_old[-1][ind3-1])


        if char==None: 
            ind2 = ind3 - 1
            char_arr=self.counts_index_new[self.k-1][ind1:ind2+1]
            #print(char_arr)
            return ind1, ind2, char_arr
        else:
            ind2 = self.counts_index_new[self.k-1].index(char, ind1)
            if ind1 == ind2:
                sum_before = 0
            else: 
                sum_before = sum(self.counts[ind1:ind2])

            if ind2 == ind3-1:
                sum_after = 0
            elif ind2 > ind3-1:
                print("error in find_index")
                sum_after = 0
            else:
                sum_after = sum(self.counts[ind2+1:ind3])

            return  sum_before, self.counts[ind2], sum_after
            
class count_mng_dyn_sta(count_mng):
    def __init__(self, alphabet_in):
        self.alphabet = alphabet_in
        self.counts = [1]*len(alphabet_in)
        self.mode = 1
        self.k = 0

    # The character is known for encoding, but currently unknown for decoding
    def get_counts(self, char = None):
        if char == None:
            return self.counts.copy()
        else:
            num_char = self.find_num_char(char)
            countret = [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])]
            self.counts[num_char] += 1
            return [countret[0], countret[1], countret[2]]
        
    # This increments the counts for the dynamic / static decoding case
    def increment_count(self, i):
        self.counts[i] +=1
        return self.alphabet[i]

class count_mng_dynamic(count_mng):
    def __init__(self, new_mode=2, first_choise = False, update_exclusion = False):
        self.alphabet = []
        self.counts = []
        self.mode = 2
        self.k = 0
        self.new_mode = new_mode
        self.first_choise = first_choise
        self.update_exclusion = update_exclusion


    def get_counts(self, excl={}, char=None):
        if char == None:
            if len(self.alphabet) == 0:
                return None
            else:
                ret_arr = self.counts.copy()
                ret_arr.append(self.get_count_new())
                return self.alphabet.copy(), ret_arr, excl
        else:
            num_char = self.find_num_char(char)

            # remove exceptions
            new_alphabet = self.alphabet.copy()
            new_counts = self.counts.copy()
            for cha in excl:
                i = new_alphabet.index(cha)
                new_alphabet.pop(i)
                new_counts.pop(i)

            if num_char > -1:
                num_char = new_alphabet.index(char)
                if self.counts[num_char] == 0:
                    countret = [sum(new_counts), self.get_count_new(alphabet=new_alphabet), 0, set(self.alphabet.copy())]
                else:
                    countret = [sum(new_counts[:num_char]), new_counts[num_char], sum(new_counts[num_char+1:])+self.get_count_new(alphabet=new_alphabet)]
                #if self.update_exclusion: self.increment_count([], char)
                return [countret[0], countret[1], countret[2], {}]
            else:
                countret = [sum(new_counts), self.get_count_new(alphabet=new_alphabet)]
                #if self.update_exclusion: self.increment_count([], char)
                return [countret[0], countret[1], 0, set(self.alphabet.copy())]

    def find_num_char(self, char):
        if char in self.alphabet:
            return self.alphabet.index(char)
        else:
            return -1
    
    def increment_count(self, context, char):
        if char in self.alphabet:
            self.counts[self.alphabet.index(char)] +=1
        else:
            self.add_new_count(char)

    # both of the following are for dynamic alphabets
    def get_count_new(self, alphabet = None):
        if alphabet is None: alphabet = self.alphabet
        modes = [1, 
                 max(1,len(alphabet)), 
                 max(1,len(alphabet)), 
                 max(1.0, len(alphabet)/2)]
        return modes[self.new_mode]
    
    def add_new_count(self, char):
        self.alphabet.append(char)
        modes = [1,
                 0,
                 1,
                 0.5]
        self.counts.append(modes[self.new_mode])

    def update_alphabet(self, char):
        self.alphabet[-1] = char

    def get_len_alphabet(self, context=[]):
        return len(self.alphabet)

#---------------------------------------------------   
from encode.ByteManagement import byte_mng_dec

class count_dynamic_k_child(count_mng_dynamic):
    def __init__(self, k:int, new_mode=2, first_choise = False, update_exclusion = False):
        count_mng_dynamic.__init__(self, new_mode, first_choise, update_exclusion)
        self.children = []
        self.k = k
        self.mode = 6

    # our new get_counts needs to go through the recursive list structure, 
    # but potentially not ....
    def get_counts(self, context, excl, char=None):
        # This is for when we begin a new count.
        if char == None:
            if len(self.alphabet) == 0:
                return None 
            if len(context) > 0 and context[0] not in self.alphabet:
                return None

        # This is when we are at the bottom of a branch
        if len(context) == 0:
            return count_mng_dynamic.get_counts(self, excl, char)
        
        # this is used for first model choise cases
        if context[0] not in self.alphabet:
            return [0,1,0,{}]

        if len(context) == 1 and self.k == len(context):
            return self.children[self.alphabet.index(context[0])].get_counts(excl, char)

        # while char is not guarenteed to be in the array, context[0] is
        # and I don't increase counts here
        return self.children[self.alphabet.index(context[0])].get_counts(context[1:], excl, char)
                
    def increment_count(self, context, char):
        if len(context) == 0:
            count_mng_dynamic.increment_count(self, [], char)
        elif context[0] not in self.alphabet:
            count_mng_dynamic.increment_count(self, [], context[0])
            self.increment_count(context, char)
        elif len(context) == 1 and self.k == len(context):
            self.children[self.alphabet.index(context[0])].increment_count([], char)
        else:
            self.children[self.alphabet.index(context[0])].increment_count(context[1:], char)

    def update_alphabet(self, context, char):
        if len(context) == 0:
            self.alphabet[-1] = char
        elif len(context) == 1 and self.k == len(context):
            self.children[self.alphabet.index(context[0])].update_alphabet(char)
        else:
            self.children[self.alphabet.index(context[0])].update_alphabet(context[1:], char)
        
    # adds the recursive structure to the class
    def add_new_count(self, char):
        count_mng_dynamic.add_new_count(self, char)
        if self.k == 1:
            new_child = count_mng_dynamic(self.new_mode)
        else:
            new_child = count_dynamic_k_child(self.k - 1, self.new_mode)
        self.children.append(new_child)

    def get_len_alphabet(self, context):
        if len(context) < 1:
            return len(self.alphabet)
        if context[0] not in self.alphabet:
            return 0
        return self.children[self.alphabet.index(context[0])].get_len_alphabet(context[1:])

# ------------------------------------------

class count_dynamic_k(count_dynamic_k_child):
    def __init__(self, k:int, new_mode=2, update_exclusion = False, first_choise = False):
        count_dynamic_k_child.__init__(self, k, new_mode, first_choise, update_exclusion)
        self.alphabet_final = -1

    def load_alphabet_dynamic(self, byte_m:byte_mng_dec):
        leng = byte_m.read_bits(8)
        self.alphabet = []
        self.counts = []
        self.children = []
        if leng == 0:
            leng = 256
        for i in range(leng):
            self.alphabet.append(byte_m.read_bits(8))
            self.counts.append(0)
            if self.k == 1:
                new_child = count_mng_dynamic(self.new_mode)
            else:
                new_child = count_dynamic_k_child(self.k - 1, self.new_mode)
            self.children.append(new_child) 
        self.alphabet_final = 0

    # our new get_counts needs to go through the recursive list structure, 
    # but potentially not ....

    def get_counts_full(self, context, char=None, excl = {}, full_context=None):
        ret_arr = []
        ret_arr.append(self.get_counts(context, excl, char))
        
        #print(context, char, ret_arr[-1])

        symbol = self.find_if_new(ret_arr[-1], char)
        context_new = context
        excl_n = excl

        # and add the next symbols
        while symbol == True and len(context_new) > 0:
            context_new = context_new[1:]
            if char is None: excl_n = excl
            else: excl_n = ret_arr[-1][-1]
            ret_arr.append(self.get_counts(context_new, excl_n, char))
            #print("v2", context_new, char, ret_arr[-1])
            symbol = self.find_if_new(ret_arr[-1], char)

        if self.first_choise and char == None:
            #print('here')
            ret_arr_2 = []
            while len(context_new) > 0:
                context_new = context_new[1:]
                if char is None: excl_n = excl
                else: excl_n = ret_arr[-1][-1]
                ret_arr_2.append(self.get_counts(context_new, excl_n, char))
            return ret_arr + ret_arr_2

        # add to the counts not accessed
        if (char is not None):
            if not self.update_exclusion:
                if full_context is not None: context = full_context
                self.increment_count([], char)
                for i in range(len(context)):
                    self.increment_count(context[i:], char)
            else:
                for i in range(len(ret_arr)): 
                    self.increment_count(context[i:], char)
                i = len(ret_arr)
                while len(context) >= i and self.get_len_alphabet(context[i:]) <= 1: # need to get alphabet length of child, not this one
                    self.increment_count(context[i:], char)
                    i += 1

        return ret_arr

    def get_count_new(self, alphabet = None):
        if self.alphabet_final > 0: alph_len = self.alphabet_final
        else: alph_len = len(self.alphabet)

        if alphabet is not None: 
            alph_dif = len(self.alphabet) - len(alphabet)
            alph_len -= alph_dif

        modes = [1, 
                 max(1,alph_len), 
                 max(1,alph_len), 
                 max(1.0, alph_len/2)]
        return modes[self.new_mode]

    def find_if_new(self, arr, char):
        if char is not None:
            if arr[2] == 0: return True
            else: return False
        else:
            if arr == None: return True
            else: return False

    # needs to be updated, it is not correct, but I need to look at the surrounding logic
    # char = -1 means new char, otherwise, char is found from the alphabet
    # context_len equals the number of elements to increment
    def increment_count_full(self, context, char, no_counts = 0):
        #print(char)
        if char == -1:
            char = self.alphabet[self.alphabet_final]
            self.alphabet_final += 1
        if not self.update_exclusion:
            for i in range(len(context)):
                self.increment_count(context[i:], char)
            self.counts[self.alphabet.index(char)] +=1
        # this is not yet correct
        else:
            if no_counts > len(context) + 1: print("context length error")
            for i in range(no_counts):
                self.increment_count(context[i:], char)
            i = no_counts
            while len(context) >= i and self.get_len_alphabet(context[i:]) <= 1: # need to get alphabet length of child, not this one
                self.increment_count(context[i:], char)
                i += 1
        #print(context, char)
        return char
    
    def get_len_alphabet(self, context):
        if len(context) < 1 and self.alphabet_final == -1:
            return len(self.alphabet)
        if len(context) < 1:
            return self.alphabet_final
        if context[0] not in self.alphabet:
            return 0
        return self.children[self.alphabet.index(context[0])].get_len_alphabet(context[1:])