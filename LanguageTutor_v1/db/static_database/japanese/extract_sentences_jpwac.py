LEVEL_MAP = {"L4" : "n5",
             "L3" : "n4",
             "L2" : "n3",
             "L1" : "n2",
             "L0" : "n1"}


def vert_to_txt(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as infile, \
        open(output_file_path, 'w', encoding='utf-8') as outfile:
        sentence = []
        
        for line in infile:
            line = line.strip()
            if not line or line.startswith('<'):
                if sentence:
                    outfile.write("".join(sentence) + "\n")
                    sentence = []
                continue
            
            parts = line.split('\t')
            if parts:
                sentence.append(parts[0])
        
        if sentence:
            outfile.write("".join(sentence) + "\n")


for jpwac_level, jlpt_level in LEVEL_MAP.items():
    vert_to_txt(f"sentences/jpWac-{jpwac_level}.vert", f"sentences/{jlpt_level}.txt")
