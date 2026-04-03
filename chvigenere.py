"""
Trabalho 1 - Cifra de Vigenère (VERSÃO FINAL - PARTE I ÍNTEGRA, PARTE II RESUMIDA)
"""

from collections import Counter
import os
import unicodedata

# ------------------------------------------------------------
# Função de normalização (REMOVE ACENTOS)
# ------------------------------------------------------------

def normalizar_ascii(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = ''.join(ch for ch in texto if unicodedata.category(ch) != 'Mn')
    return texto.upper()


# ------------------------------------------------------------
# Parte I: Cifrador / Decifrador de Vigenère
# ------------------------------------------------------------

def encriptar_vigenere(textobase: str, chave: str) -> str:
    textobase = normalizar_ascii(textobase)
    chave = normalizar_ascii(chave)

    resultado = []
    chave_len = len(chave)
    chave_idx = 0

    for ch in textobase:
        if 'A' <= ch <= 'Z':
            p = ord(ch) - ord('A')
            k = ord(chave[chave_idx % chave_len]) - ord('A')
            c = (p + k) % 26
            resultado.append(chr(c + ord('A')))
            chave_idx += 1
        else:
            resultado.append(ch)

    return ''.join(resultado)


def decifrar_vigenere(textocifrado: str, chave: str) -> str:
    textocifrado = normalizar_ascii(textocifrado)
    chave = normalizar_ascii(chave)

    resultado = []
    chave_len = len(chave)
    chave_idx = 0

    for ch in textocifrado:
        if 'A' <= ch <= 'Z':
            c = ord(ch) - ord('A')
            k = ord(chave[chave_idx % chave_len]) - ord('A')
            p = (c - k) % 26
            resultado.append(chr(p + ord('A')))
            chave_idx += 1
        else:
            resultado.append(ch)

    return ''.join(resultado)


# ------------------------------------------------------------
# Parte II: Ataque por análise de frequência
# ------------------------------------------------------------

FREQ_PT = {
    'A': 14.63, 'B': 1.04, 'C': 3.88, 'D': 4.99, 'E': 12.57,
    'F': 1.02, 'G': 1.30, 'H': 1.28, 'I': 6.18, 'J': 0.40,
    'K': 0.02, 'L': 2.78, 'M': 4.74, 'N': 5.05, 'O': 10.73,
    'P': 2.52, 'Q': 1.20, 'R': 6.53, 'S': 7.81, 'T': 4.34,
    'U': 4.63, 'V': 1.67, 'W': 0.01, 'X': 0.21, 'Y': 0.01,
    'Z': 0.47
}

FREQ_EN = {
    'A': 8.17, 'B': 1.49, 'C': 2.78, 'D': 4.25, 'E': 12.70,
    'F': 2.23, 'G': 2.02, 'H': 6.09, 'I': 6.97, 'J': 0.15,
    'K': 0.77, 'L': 4.03, 'M': 2.41, 'N': 6.75, 'O': 7.51,
    'P': 1.93, 'Q': 0.10, 'R': 5.99, 'S': 6.33, 'T': 9.06,
    'U': 2.76, 'V': 0.98, 'W': 2.36, 'X': 0.15, 'Y': 1.97,
    'Z': 0.07
}

PALAVRAS_PT = {"DE","DA","DO","E","A","O","QUE","EM","UM","UMA","PARA","COM"}
PALAVRAS_EN = {"THE","AND","OF","TO","IN","IS","YOU","THAT","IT","FOR"}


def encontrar_letra_chave(seq: str, freq_idioma: dict):
    seq = ''.join(ch for ch in normalizar_ascii(seq) if 'A' <= ch <= 'Z')
    if not seq:
        return 'A', 0.0

    n = len(seq)
    contagens = Counter(seq)

    melhor_shift = 0
    melhor_chi2 = float('inf')

    for shift in range(26):
        chi2 = 0.0
        for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            observado = contagens.get(letra, 0)
            letra_clara = chr((ord(letra) - ord('A') - shift) % 26 + ord('A'))
            esperado = n * (freq_idioma[letra_clara] / 100.0)
            if esperado > 0:
                chi2 += (observado - esperado) ** 2 / esperado

        if chi2 < melhor_chi2:
            melhor_chi2 = chi2
            melhor_shift = shift

    return chr(melhor_shift + ord('A')), melhor_chi2


def score_palavras(texto: str, idioma: str):
    palavras = texto.split()
    base = PALAVRAS_PT if idioma == 'pt' else PALAVRAS_EN
    return sum(1 for p in palavras if p in base)


def atacar_vigenere(textocifrado: str, idioma: str, max_len=20):
    texto_limpo = normalizar_ascii(textocifrado)
    apenas_letras = ''.join(ch for ch in texto_limpo if 'A' <= ch <= 'Z')
    freq = FREQ_PT if idioma == 'pt' else FREQ_EN

    melhores = []
    for tamanho in range(1, max_len + 1):
        chave = []
        chi_total = 0
        for i in range(tamanho):
            seq = apenas_letras[i::tamanho]
            letra, chi2 = encontrar_letra_chave(seq, freq)
            chave.append(letra)
            chi_total += chi2
        chave_str = ''.join(chave)
        texto_decifrado = decifrar_vigenere(textocifrado, chave_str)
        score = chi_total - 8 * score_palavras(texto_decifrado, idioma)
        melhores.append((score, chave_str, texto_decifrado))

    melhores.sort(key=lambda x: x[0])
    return melhores[0][1], melhores[0][2]   # retorna apenas chave e texto


def atacar_arquivo(nome_arquivo: str, idioma: str):
    if not os.path.exists(nome_arquivo):
        print(f"Arquivo não encontrado: {nome_arquivo}")
        return
    with open(nome_arquivo, 'r', encoding='utf-8') as f:
        cifrado = f.read()
    chave, texto = atacar_vigenere(cifrado, idioma, max_len=20)
    print(f"\n--- {nome_arquivo} ({idioma.upper()}) ---")
    print(f"Chave recuperada: {chave}")
    print("Texto decifrado (primeiros 500 caracteres):")
    print(texto[:500])
    if len(texto) > 500:
        print("... (truncado)")


def demonstrar_ataque_com_texto_longo():
    print("\n[DEMONSTRAÇÃO] Texto longo em português:")
    exemplo_longo = (
        "A CIFRA DE VIGENERE FOI INVENTADA NO SECULO XVI PELO CRIPTOGRAFO FRANCES "
        "BLAISE DE VIGENERE. ESTE METODO FOI CONSIDERADO INQUEBRAVEL DURANTE MUITOS ANOS. "
        "A TECNICA UTILIZA UMA CHAVE QUE SE REPETE CICLICAMENTE PARA DESLOCAR CADA LETRA. "
        "PARA QUEBRAR A CIFRA, USA-SE ANALISE DE FREQUENCIA DAS LETRAS. QUANTO MAIOR O TEXTO, "
        "MAIS PRECISA E A RECUPERACAO DA CHAVE. ESTE TRABALHO DEMONSTRA NA PRATICA O FUNCIONAMENTO "
        "DA CIFRA E DO ATAQUE POR FREQUENCIA, ATENDENDO AOS REQUISITOS DA DISCIPLINA."
    )
    chave_real = "SEGURANCA"
    cifrado_demo = encriptar_vigenere(exemplo_longo, chave_real)
    chave_rec, texto_rec = atacar_vigenere(cifrado_demo, "pt")
    print(f"Chave real:      {chave_real}")
    print(f"Chave recuperada: {chave_rec}")
    print("Texto decifrado (primeiros 300 caracteres):")
    print(texto_rec[:300])
    if chave_rec == chave_real.upper():
        print(">>> Ataque bem-sucedido! <<<")
    else:
        print(">>> Falha (texto muito curto ou chave longa demais?) <<<")

#--------------------------------------
#Main
#--------------------------------------

def main():
    print("=" * 60)
    print("Parte I - Cifragem e Decifragem de Vigenère")
    print("=" * 60)
    print("===== CIFRAGEM =====")
    txt = "EXEMPLO DE TEXTO PRA CIFRAR"
    chave = "BATATA"
    print(f"Texto claro: {txt}")
    print(f"Chave: {chave}")
    cifrado = encriptar_vigenere(txt, chave)
    print(f"Texto cifrado: {cifrado}")
    decifrado = decifrar_vigenere(cifrado, chave)
    print(f"Texto decifrado: {decifrado}")
    
    print("===== DECIFRAGEM =====")
    cripat = "UEQTH PSA WEVIGRTR"
    print(f"Texto cifrado: {cripat}")
    descript_especifico = decifrar_vigenere(cripat, chave)
    print(f"Texto decifrado: {descript_especifico}")
    print()

    print("\n" + "=" * 60)
    print("Parte II - Ataque por análise de frequência")
    print("=" * 60)

    atacar_arquivo("mensagem_portugues_cifrada.txt", "pt")
    atacar_arquivo("mensagem_ingles_cifrada.txt", "en")

    if not (os.path.exists("mensagem_portugues_cifrada.txt") or
            os.path.exists("mensagem_ingles_cifrada.txt")):
        demonstrar_ataque_com_texto_longo()

    print("\nFim do programa.")


if __name__ == "__main__":
    main() 
