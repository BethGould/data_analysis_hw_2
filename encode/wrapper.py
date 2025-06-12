from encode.CountManagement import count_dynamic_k
from encode.ByteManagement import byte_mng_dec
from encode.ArithmeticEncoder import arith_code_enc_k
from encode.ArithmeticDecoder import arith_code_dec_k
from encode.HelperFunctions import find_k

def run_encoder(import_file, export_file, k = None, N = 64, update_exclusion = False, first_choise = False):

    N = int(N // 8) * 8

    if k < 0: k = 0
    if N < 8: N = 8

    with open(import_file, 'rb') as f:
        text = f.read()

    if k is None:
        k = find_k(text)

    counts = count_dynamic_k(k, new_mode=2, update_exclusion=update_exclusion, first_choise=first_choise)
    encoder_new = arith_code_enc_k(counts, N)

    for i in text:
        encoder_new.add_character(i)

    whitespace2 = encoder_new.finalize()

    byte_arr = [whitespace2, k, int(N // 8)]
    if update_exclusion: byte_arr[0] += 128
    if first_choise: byte_arr[1] += 128
    byte_arr.append(len(encoder_new.count_m.alphabet))
    if byte_arr[1] > 255: byte_arr[1] = 0
    for i in encoder_new.count_m.alphabet: byte_arr.append(i)

    with open(export_file, "wb") as f:
        f.write(bytearray(byte_arr))
        f.write(bytearray(encoder_new.byte_encode.byte_store))

def run_decoder(import_file, export_file):
    byte_m = byte_mng_dec()
    byte_m.load_file(import_file)
    update_exclusion = (byte_m.read_bits(1) == 1)
    whitespace = byte_m.read_bits(7)
    first_choise = (byte_m.read_bits(1) == 1)
    k = byte_m.read_bits(7)
    N = byte_m.read_bits(8) * 8
    counts_d = count_dynamic_k(k, new_mode=2, update_exclusion=update_exclusion, first_choise=first_choise)
    counts_d.load_alphabet_dynamic(byte_m)

    decoder_new = arith_code_dec_k(counts_d, byte_m, whitespace, N)
    cond = decoder_new.cont()

    array = []

    while cond:
    #for i in range(lim):
        array.append(decoder_new.remove_character())
        cond = decoder_new.cont()
    
    with open(export_file, "wb") as f:
        f.write(bytearray(array))