
# ---------------------------------------------------------------------------
# Old versions of the code.

from encode import count_mng

class count_mng_dynamic_old(count_mng):
    def __init__(self, new_mode=2):
        self.alphabet = []
        self.counts = []
        self.mode = 2
        self.k = 0
        self.new_mode = new_mode

    def get_counts(self, char=None):
        if char == None:
            if len(self.alphabet) == 0:
                return None
            else:
                ret_arr = self.counts.copy()
                ret_arr.append(self.get_count_new())
                return ret_arr
        else:
            num_char = self.find_num_char(char)
            if num_char < len(self.alphabet):
                if self.counts[num_char] == 0:
                    countret = [sum(self.counts), self.get_count_new(), 0]
                else:
                    countret = [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])+self.get_count_new()]
                self.counts[num_char] += 1
                return [countret[0], countret[1], countret[2]]
            else:
                countret = [sum(self.counts), self.get_count_new()]
                self.add_new_count(char)
                return [countret[0], countret[1], 0]

    def find_num_char(self, char):
        if char not in self.alphabet:
            return len(self.alphabet)
        else:
            return self.alphabet.index(char)

    def increment_count(self, i):
        if len(self.alphabet)==0:
            self.add_new_count(0)
        elif i < len(self.alphabet):
            self.counts[i] +=1
        else:
            self.add_new_count(i)
        return self.alphabet[i]
    
    # both of the following are for dynamic alphabets
    def get_count_new(self):
        modes = [1, 
                 max(1,len(self.alphabet)), 
                 max(1,len(self.alphabet)), 
                 max(1.0, len(self.alphabet)/2)]
        return modes[self.new_mode]
    
    def add_new_count(self, char):
        self.alphabet.append(char)
        modes = [1,
                 0,
                 1,
                 0.5]
        self.counts.append(modes[self.new_mode])

class count_mng_dec_old:
    # defines three modes 
    # 0 means static counts,
    # 1 means dynamic, fixed alphabet
    # 2 means dynamic alphabet
    # new_mode defines the count of the letter 'new' in the dynamic alphabet
    def __init__(self,alphabet_in=None, counts_in=None, new_mode=2):
        self.mode = 0
        if alphabet_in == None:
            self.mode = 2
            self.alphabet = []
            self.counts = []
        elif counts_in == None:
            self.mode = 1
            self.alphabet = alphabet_in
            self.counts = [1]*len(alphabet_in)
        else:
            self.mode = 0
            self.alphabet = alphabet_in
            self.counts = counts_in
        self.new_mode = new_mode

    def increment_count(self, i):
        if len(self.alphabet)==0:
            self.add_new_count(0)
        elif i < len(self.alphabet):
            self.counts[i] +=1
        else:
            self.add_new_count(i)
        return self.alphabet[i]

    #update
    def get_counts(self):
        if self.mode == 0: return self.get_counts_0()
        elif self.mode == 1: return self.get_counts_0()
        else: return self.get_counts_2()

    def get_counts_0(self):
        return self.counts.copy()
    
    # this is the most complicated case
    # I need to find the structure here and add it
    def get_counts_2(self):
        if len(self.alphabet) == 0:
            return None
        else:
            ret_arr = self.counts.copy()
            ret_arr.append(self.get_count_new())
            #print(ret_arr)
            return ret_arr
        
    # both of the following are for dynamic alphabets
    def get_count_new(self):
        modes = [1, 
                 max(1,len(self.alphabet)), 
                 max(1,len(self.alphabet)), 
                 max(1.0, len(self.alphabet)/2)]
        return modes[self.new_mode]
    
    def add_new_count(self, char):
        self.alphabet.append(char)
        modes = [1,
                 0,
                 1,
                 0.5]
        self.counts.append(modes[self.new_mode])


class count_mng_enc_old:
    # defines three modes 
    # 0 means static counts,
    # 1 means dynamic, fixed alphabet
    # 2 means dynamic alphabet
    # new_mode defines the count of the letter 'new' in the dynamic alphabet
    def __init__(self,alphabet_in=None, counts_in=None, new_mode=2):
        self.mode = 0
        if alphabet_in == None:
            self.mode = 2
            self.alphabet = []
            self.counts = []
        elif counts_in == None:
            self.mode = 1
            self.alphabet = alphabet_in
            self.counts = [1]*len(alphabet_in)
        else:
            self.mode = 0
            self.alphabet = alphabet_in
            self.counts = counts_in
        self.new_mode = new_mode

    def get_counts(self, char):
        num_char = self.find_num_char(char)
        if self.mode == 0: return self.get_counts_0(num_char)
        elif self.mode == 1: return self.get_counts_1(num_char)
        else: return self.get_counts_2(num_char, char)

    def get_counts_0(self,num_char):
        return [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])]
    
    def get_counts_1(self,num_char):
        countret = [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])]
        self.counts[num_char] += 1
        return [countret[0], countret[1], countret[2]]
    
    # this is the most complicated case
    # I need to find the structure here and add it
    def get_counts_2(self,num_char, char):
        if num_char < len(self.alphabet):
            if self.counts[num_char] == 0:
                countret = [sum(self.counts), self.get_count_new(), 0]
            else:
                countret = [sum(self.counts[:num_char]), self.counts[num_char], sum(self.counts[num_char+1:])+self.get_count_new()]
            self.counts[num_char] += 1
            return [countret[0], countret[1], countret[2]]
        else:
            countret = [sum(self.counts), self.get_count_new()]
            self.add_new_count(char)
            return [countret[0], countret[1], 0]
        
    # both of the following are for dynamic alphabets
    def get_count_new(self):
        modes = [1, 
                 max(1,len(self.alphabet)), 
                 max(1,len(self.alphabet)), 
                 max(1.0, len(self.alphabet)/2)]
        return modes[self.new_mode]
    
    def add_new_count(self, char):
        self.alphabet.append(char)
        modes = [1,
                 0,
                 1,
                 0.5]
        self.counts.append(modes[self.new_mode])

    # this will need to return the corresponding index in the alphabet for the number
    # in the case of mode == 2, I need to return len(alphabet) for char not in alphabet
    def find_num_char(self, char):
        if self.mode == 2 and char not in self.alphabet:
            return len(self.alphabet)
        else:
            return self.alphabet.index(char)
        