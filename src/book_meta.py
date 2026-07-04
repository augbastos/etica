"""Metadados compartilhados do livro (usado por build_pdf e build_epub)."""

TITLE = "Ética"
SUBTITLE = ("Spinoza para o século XXI — uma leitura moderna da obra "
            "que dissolveu a fronteira entre Deus e a Natureza")
AUTHOR = "Benedictus de Spinoza"
EDITION = "Edição modernizada · 2026"
LANG = "pt-BR"

# ordem das partes: (n, título exibido, epígrafe, referência da epígrafe, svg de abertura)
PARTS = [
    (1, "Deus,<br>ou a Natureza",
     "Tudo o que existe, existe em Deus; e nada pode ser, nem ser concebido, sem Deus.",
     "Proposição XV", "part-opener-1.svg"),
    (2, "A Mente",
     "A ordem e a conexão das ideias é a mesma que a ordem e a conexão das coisas.",
     "Proposição VII", "part-opener-2.svg"),
    (3, "Os Afetos",
     "Cada coisa se esforça, tanto quanto está em si, por perseverar em seu ser.",
     "Proposição VI", "part-opener-3.svg"),
    (4, "A Servidão",
     "O homem livre em nada pensa menos do que na morte.",
     "Proposição LXVII", "part-opener-4.svg"),
    (5, "A Liberdade",
     "A beatitude não é o prêmio da virtude, mas a própria virtude.",
     "Proposição XLII", "part-opener-5.svg"),
]
