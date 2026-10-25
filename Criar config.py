import json, os

print("=" * 50)
print("  CRIADOR DE config.json — Bot de Vendas")
print("=" * 50)
print("(deixe em branco pra pular e editar depois)\n")

def ask(label, tipo="str"):
    v = input(f"{label}: ").strip()
    if tipo == "int":
        try: return int(v) if v else 0
        except: return 0
    return v

cfg = {
    "token":              ask(" "),
    "owner":              ask("  ", "int"),
    "guild_id":           ask("   ", "int"),
    "color":              5763719,
    "nome":               ask(" Devhub ") or "Devhub ",
    "footer":             ask("Devhub") or "Todos os direitos reservados",
    "categoria":          ask("", "int"),
    "logs":               ask("", "int"),
    "modo_pagamento":     ask("Modo manual") or "manual",
    "pix_chave":          ask(" "),
    "pix_nome":           ask(" "),
    "pix_cidade":         ask("Sao Paulo )"),
    "confirmacao_canal":  ask(" ", "int"),
    "accessToken":        ask("Token do Mercado Pago (só se modo=auto)"),
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=4, ensure_ascii=False)

print("\n✅ config.json criado com sucesso!")
print("Arquivo salvo em:", os.path.abspath("config.json"))
