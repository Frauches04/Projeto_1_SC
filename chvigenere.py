"""
Trabalho 1 - Cifra de Vigenère (VERSÃO FINAL - COM ÍNDICE DE COINCIDÊNCIA)
"""

from collections import Counter
import os
import unicodedata

# Função para remover acentos e normalizar para maiúsculas 
def normalizar_ascii(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)# Remove os acentos 
    texto = ''.join(ch for ch in texto if unicodedata.category(ch) != 'Mn') 
    return texto.upper()#Converte para maiúsculas e remove acentos


# Parte I: Cifrador / Decifrador

def encriptar_vigenere(textobase: str, chave: str) -> str:
    textobase = normalizar_ascii(textobase) # Normaliza o texto base
    chave = normalizar_ascii(chave)# Normaliza a chave

    resultado = [] # Lista para construir o resultado cifrado
    chave_len = len(chave) # Comprimento da chave para repetição
    chave_idx = 0 # Índice para percorrer a chave

    for ch in textobase: 
        if 'A' <= ch <= 'Z': # Apenas letras são cifradas e maiúsculas
            p = ord(ch) - ord('A') # Converte a letra para um número (0-25)
            k = ord(chave[chave_idx % chave_len]) - ord('A') # Obtém a letra da chave correspondente (repetindo se necessário)
            c = (p + k) % 26 # aplica a cifra de Vigenère (soma e módulo 26)
            resultado.append(chr(c + ord('A'))) # Converte de volta para letra e adiciona ao resultado
            chave_idx += 1 #avança o contador da chave
        else:  # Caracteres não alfabéticos são mantidos inalterados
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
            c = ord(ch) - ord('A') # Converte a letra cifrada para um número (0-25)
            k = ord(chave[chave_idx % chave_len]) - ord('A') # Obtém a letra da chave correspondente (repetindo se necessário)
            p = (c - k) % 26 # Aplica a decifragem de Vigenère (subtração e módulo 26)
            resultado.append(chr(p + ord('A')))
            chave_idx += 1
        else:
            resultado.append(ch)

    return ''.join(resultado)


# ------------------------------------------------------------
# Parte II: Ataque por análise de frequência

#Frequencias de letras para português e inglês
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

# Palavras comuns para auxiliar
PALAVRAS_PT = {"DE","DA","DO","E","A","O","QUE","EM","UM","UMA","PARA","COM"}
PALAVRAS_EN = {"THE","AND","OF","TO","IN","IS","YOU","THAT","IT","FOR"}



# Calculo do índice de Coincidência (IC)
def calcular_ic(sequencia: str) -> float:
    sequencia = ''.join(ch for ch in sequencia if 'A' <= ch <= 'Z') # Apenas letras maiúsculas
    n = len(sequencia) # n recebe o N° total de letras na sequência
    if n < 2: # Evita divisão por zero caso a sequência seja muito curta
        return 0.0
    cont = Counter(sequencia) # Conta a frequência de cada letra na sequência
    soma = sum(f * (f - 1) for f in cont.values()) #Calcula a frequencia de cada letra usando a fórmula f*(f-1) e soma os resultados
    return soma / (n * (n - 1)) # Retorna o IC calculado usando a fórmula final


#Estimar o tamanho da chave usando o IC médio
def encontrar_periodo_por_ic(texto: str, idioma: str, max_len=20) -> int:
    
    texto_limpo = ''.join(ch for ch in normalizar_ascii(texto) if 'A' <= ch <= 'Z')
    alvo = 0.066 if idioma == 'pt' else 0.067 #Define o IC esperadopara cada idioma (português ou inglês)
    melhor_tam = 1 #Inicializa o melhor tamanho de chave encontrado
    melhor_dist = float('inf') #Inicializa a melhor distância (diferença entre IC médio e alvo) 
    
    for L in range(1, max_len + 1): #Testa cada tamanho de chave possível de 1 até max_len
        ics = [] #Lista para armazenar os ICs de cada coluna
        for i in range(L): #Cria as colunas do texto cifrado para o tamanho de chave atual (L) e calcula o IC de cada coluna
            coluna = texto_limpo[i::L] #Extrai a coluna correspondente ao tamanho de chave atual (L) e posição i
            if len(coluna) > 1: #Calcula o IC apenas se a coluna tiver mais de 1 letra (para evitar casos de divisão por zero)
                ics.append(calcular_ic(coluna))
        if not ics: # Se nenhuma coluna tiver mais de 1 letra,
            continue
        ic_medio = sum(ics) / len(ics) #calcula o IC médio para o tamanho de chave atual (L)
        dist = abs(ic_medio - alvo) #Calcula a distância absoluta entre ICs
        if dist < melhor_dist: #atualiza o melhor tamanho de chave encontrado se a distância for menor que a melhor distância anterior
            melhor_dist = dist
            melhor_tam = L
    return melhor_tam #Retorna o melhor tamanho de chave encontrado com base no IC médio

# Encontrar letra da chave por chi-quadrado
def encontrar_letra_chave(seq: str, freq_idioma: dict):
    seq = ''.join(ch for ch in normalizar_ascii(seq) if 'A' <= ch <= 'Z')
    if not seq: #Se a sequência estiver vazia, retorna 'A' e chi2 zero.
        return 'A', 0.0 

    n = len(seq) #Número total de letras na sequência
    contagens = Counter(seq) #Contagem de cada letra na sequência
    melhor_shift = 0 #Inicializa o melhor deslocamento encontrado
    melhor_chi2 = float('inf') #Inicializa o melhor valor de chi-quadrado encontrado (infinito para garantir que qualquer valor calculado seja menor)

    for shift in range(26): #Testa cada possível deslocamento (0 a 25) para encontrar a letra da chave que melhor se encaixa na distribuição de frequências do idioma
        chi2 = 0.0 #zera o valor de chi-quadrado para o deslocamento atual
        for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ': #percorre todas as letras do alfabeto
            observado = contagens.get(letra, 0) #obseerva a repetição da letra
            letra_clara = chr((ord(letra) - ord('A') - shift) % 26 + ord('A')) #calcula a letra clara que originou a cifrada
            esperado = n * (freq_idioma[letra_clara] / 100.0) #Frequência esperada dessa letra clara
            if esperado > 0: #Se o valor esperado for positivo, contribui com (obs - esp)² / esp para o chi2.
                chi2 += (observado - esperado) ** 2 / esperado
        if chi2 < melhor_chi2: #Se o chi2 deste shift for menor que o melhor encontrado até agora, atualiza.
            melhor_chi2 = chi2
            melhor_shift = shift
    #Retorna a letra da chave correspondente ao melhor shift e o valor do chi2.
    return chr(melhor_shift + ord('A')), melhor_chi2

# Ataque principal (usando IC + chi-quadrado) - VERSÃO CORRIGIDA COM SCORE DE PALAVRAS
def atacar_vigenere(textocifrado: str, idioma: str, max_len=30):
    texto_limpo = normalizar_ascii(textocifrado)
    apenas_letras = ''.join(ch for ch in texto_limpo if 'A' <= ch <= 'Z')
    if not apenas_letras: #Se não houver nenhuma letra, retorna chave e texto vazios.
        return '', ''
    
    #Estimar o tamanho da chave pelo IC
    tamanho_ic = encontrar_periodo_por_ic(apenas_letras, idioma, max_len)
    print(f"[Tamanho estimado pelo IC: {tamanho_ic}]")
    
    # Coletar candidatos: o próprio tamanho e seus divisores
    candidatos = set()
    candidatos.add(tamanho_ic)
    for d in range(2, int(tamanho_ic**0.5) + 1):
        if tamanho_ic % d == 0:
            candidatos.add(d)
            candidatos.add(tamanho_ic // d)
    candidatos = sorted(candidatos)
    print(f"[Testando tamanhos candidatos: {candidatos}]")
    
    freq = FREQ_PT if idioma == 'pt' else FREQ_EN
    base_palavras = PALAVRAS_PT if idioma == 'pt' else PALAVRAS_EN
    
    melhor_score = -1e9   # score maior é melhor
    melhor_chave = ''
    melhor_texto = ''
    
    for L in candidatos: #Para cada tamanho candidato
        chave = [] #lista vazia das letras da chave recuperada
        chi_total = 0
        for i in range(L): #Cria as colunas do texto cifrado para o tamanho de chave estimado e encontra a letra da chave correspondente a cada coluna usando chi-quadrado
            coluna = apenas_letras[i::L]
            letra, chi2 = encontrar_letra_chave(coluna, freq)
            chave.append(letra)#Descobre a letra da chave para essa coluna e adiciona à lista.
            chi_total += chi2
        chave_str = ''.join(chave) #Concatena as letras para formar a chave completa.
        texto_decifrado = decifrar_vigenere(textocifrado, chave_str)
        # Conta palavras comuns no texto decifrado (ignora pontuação)
        palavras = [p.strip(".,;:!?()[]{}'\"") for p in texto_decifrado.upper().split()]
        num_palavras = sum(1 for p in palavras if p in base_palavras)
        # Score: quanto menor o chi² e maior o número de palavras comuns, melhor
        score = -chi_total + 10.0 * num_palavras
        if score > melhor_score:
            melhor_score = score
            melhor_chave = chave_str
            melhor_texto = texto_decifrado
    
    print(f"[Tamanho escolhido: {len(melhor_chave)}]")
    return melhor_chave, melhor_texto#Decifra o texto original usando a chave recuperada e retorna a chave e o texto decifrado.

# Funções auxiliares para demonstração e ataque em arquivos

def atacar_arquivo(nome_arquivo: str, idioma: str):#Recebe o nome do arquivo e o idioma.
    if not os.path.exists(nome_arquivo):
        print(f"Arquivo não encontrado: {nome_arquivo}")
        return#Se o arquivo não existir, exibe uma mensagem e retorna sem fazer nada.
    with open(nome_arquivo, 'r', encoding='utf-8') as f:
        cifrado = f.read()#Abre o arquivo em modo leitura ('r') com codificação UTF‑8 e lê todo o conteúdo para a string cifrado.
    chave, texto = atacar_vigenere(cifrado, idioma, max_len=30) 
    #Exibe o nome do arquivo, o idioma, a chave recuperada e os primeiros 500 caracteres do texto decifrado (com indicação de truncamento se o texto for muito longo).
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


def demonstrar_ataque_com_texto_longo_en():
    print("\n[DEMONSTRAÇÃO] Texto longo em inglês:")
    exemplo_longo_en = (
        "THE VIGENERE CIPHER WAS INVENTED IN THE SIXTEENTH CENTURY BY THE FRENCH "
        "CRYPTOGRAPHER BLAISE DE VIGENERE. THIS METHOD WAS CONSIDERED UNBREAKABLE "
        "FOR MANY YEARS AND WAS CALLED 'LE CHIFFRE INDECHIFFRABLE'. THE TECHNIQUE "
        "USES A KEY THAT REPEATS CYCLICALLY TO SHIFT EACH LETTER OF THE ORIGINAL "
        "TEXT. THE SECURITY OF THE CIPHER RESTS ON THE LENGTH AND UNPREDICTABILITY "
        "OF THE KEY. TO BREAK THIS CIPHER, CRYPTANALYSTS USE LETTER FREQUENCY "
        "ANALYSIS, WHICH EXPLOITS THE STATISTICAL CHARACTERISTICS OF EACH LANGUAGE. "
        "THE LONGER THE CIPHER TEXT, THE MORE ACCURATE THE KEY RECOVERY. THIS "
        "ACADEMIC WORK DEMONSTRATES PRACTICALLY THE OPERATION OF THE CIPHER AND "
        "THE FREQUENCY ATTACK, MEETING THE REQUIREMENTS OF THE COURSE. ADDITIONAL "
        "SENTENCES ARE INCLUDED TO INCREASE THE TOTAL LENGTH OF THE TEXT, ENSURING "
        "THAT THE FREQUENCY DISTRIBUTION APPROACHES THE THEORETICAL VALUES. THIS "
        "MAKES THE ATTACK MORE RELIABLE AND DEMONSTRATES THE EFFECTIVENESS OF THE "
        "METHOD EVEN FOR MODERATELY SIZED CIPHERTEXTS."
    )
    chave_real_en = "CRYPTO"
    cifrado_demo_en = encriptar_vigenere(exemplo_longo_en, chave_real_en)
    chave_rec_en, texto_rec_en = atacar_vigenere(cifrado_demo_en, "en")
    print(f"Chave real:      {chave_real_en}")
    print(f"Chave recuperada: {chave_rec_en}")
    print("Texto decifrado (primeiros 400 caracteres):")
    print(texto_rec_en[:400])
    if chave_rec_en == chave_real_en.upper():
        print(">>> Ataque bem-sucedido! <<<")
    else:
        print(">>> Ainda com erro, mas o texto está maior. Tente aumentar mais se necessário.")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
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
        demonstrar_ataque_com_texto_longo_en()   

    print("\nFim do programa.")


if __name__ == "__main__":
    main()