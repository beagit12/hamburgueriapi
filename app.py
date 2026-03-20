import streamlit as st
import sqlite3
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# -------------------------
# BANCO DE DADOS
# -------------------------

conn = sqlite3.connect("pedidos.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    lanche TEXT,
    bebida TEXT,
    preco REAL,
    status TEXT
)
""")

# -------------------------
# CARRINHO
# -------------------------

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

# -------------------------
# MENU LATERAL
# -------------------------

pagina = st.sidebar.selectbox(
    "📋 Menu",
    ["Fazer pedido", "Cozinha", "Relatório"]
)

# -------------------------
# CARDÁPIO
# -------------------------

menu_lanches = {
    "X-Burger": 15,
    "X-Salada": 18,
    "X-Bacon": 20,
    "X-Tudo": 25
}

menu_bebidas = {
    "Coca-Cola": 6,
    "Guaraná": 5,
    "Suco": 7,
    "Água": 4
}

menu_batatas = {
    "Batata P": 8,
    "Batata G": 12
}

# -------------------------
# FAZER PEDIDO
# -------------------------

if pagina == "Fazer pedido":

    st.title("🍔 Hamburgueria Univesp")

    nome = st.text_input("Nome do cliente")

    lanche = st.selectbox("Escolha seu hambúrguer", list(menu_lanches.keys()))

    # BEBIDA OPCIONAL
    opcoes_bebida = ["Sem bebida"] + list(menu_bebidas.keys())
    bebida = st.selectbox("Escolha sua bebida (opcional)", opcoes_bebida)

    if bebida == "Sem bebida":
        preco_bebida = 0
    else:
        preco_bebida = menu_bebidas[bebida]

    # BATATA OPCIONAL
    opcoes_batata = ["Sem batata"] + list(menu_batatas.keys())
    batata = st.selectbox("Deseja batata?", opcoes_batata)

    if batata == "Sem batata":
        preco_batata = 0
    else:
        preco_batata = menu_batatas[batata]

    # PREÇO TOTAL
    preco_total = menu_lanches[lanche] + preco_bebida + preco_batata

    st.write(f"💰 Total: R$ {preco_total}")

    if st.button("Adicionar ao carrinho"):

        item = {
            "lanche": lanche,
            "bebida": bebida,
            "batata": batata,
            "preco": preco_total
        }

        st.session_state.carrinho.append(item)

        st.success("Item adicionado!")

    # -------------------------
    # CARRINHO
    # -------------------------

    st.subheader("🛒 Carrinho")

    if len(st.session_state.carrinho) == 0:
        st.write("Carrinho vazio")

    else:
        total = 0

        for i, item in enumerate(st.session_state.carrinho):

            col1, col2 = st.columns([4,1])

            with col1:

                descricao = item["lanche"]

                if item["bebida"] != "Sem bebida":
                    descricao += f" + {item['bebida']}"

                if item["batata"] != "Sem batata":
                    descricao += f" + {item['batata']}"

                st.write(f"{descricao} - R$ {item['preco']}")

            with col2:
                if st.button("❌", key=i):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

            total += item["preco"]

        st.write(f"### 💰 Total do carrinho: R$ {total}")

        if st.button("Finalizar pedido"):

            if nome == "":
                st.warning("Digite o nome do cliente")

            else:

                for item in st.session_state.carrinho:

                    cursor.execute(
                        "INSERT INTO pedidos (nome, lanche, bebida, preco, status) VALUES (?, ?, ?, ?, ?)",
                        (
                            nome,
                            item["lanche"],
                            item["bebida"],
                            item["preco"],
                            "Em preparo"
                        )
                    )

                conn.commit()

                st.session_state.carrinho = []

                st.success("🎉 Pedido enviado para a cozinha!")
                st.balloons()

# -------------------------
# COZINHA
# -------------------------

if pagina == "Cozinha":

    st.title("👨‍🍳 Painel da cozinha")

    st_autorefresh(interval=5000, key="refresh")

    cursor.execute("SELECT * FROM pedidos")
    pedidos = cursor.fetchall()

    df = pd.DataFrame(
        pedidos,
        columns=["ID","Cliente","Lanche","Bebida","Preco","Status"]
    )

    if df.empty:
        st.info("Nenhum pedido ainda.")

    else:
        for _, row in df.iterrows():

            st.markdown("---")

            col1, col2 = st.columns([3,1])

            with col1:
                st.write(f"### Pedido #{row['ID']}")
                st.write(f"👤 Cliente: {row['Cliente']}")
                st.write(f"🍔 Lanche: {row['Lanche']}")
                st.write(f"🥤 Bebida: {row['Bebida']}")
                st.write(f"💰 Preço: R$ {row['Preco']}")

            with col2:

                status = row["Status"]

                if status == "Em preparo":
                    cor = "🟡"
                elif status == "Pronto":
                    cor = "🟢"
                else:
                    cor = "⚪"

                st.write(f"{cor} {status}")

    st.subheader("Atualizar status")

    id_pedido = st.number_input("ID do pedido", min_value=1)

    novo_status = st.selectbox(
        "Novo status",
        ["Em preparo", "Pronto", "Entregue"]
    )

    if st.button("Atualizar"):
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, id_pedido)
        )

        conn.commit()
        st.success("Status atualizado!")

# -------------------------
# RELATÓRIO
# -------------------------

if pagina == "Relatório":

    st.title("📊 Relatório de vendas")

    cursor.execute("SELECT * FROM pedidos")
    pedidos = cursor.fetchall()

    df = pd.DataFrame(
        pedidos,
        columns=["ID","Cliente","Lanche","Bebida","Preco","Status"]
    )

    st.dataframe(df)

    if not df.empty:

        faturamento_total = df["Preco"].sum()
        ticket_medio = df["Preco"].mean()
        lanche_top = df["Lanche"].value_counts().idxmax()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Faturamento", f"R$ {faturamento_total:.2f}")

        with col2:
            st.metric("📦 Pedidos", len(df))

        with col3:
            st.metric("🏆 Mais vendido", lanche_top)

        st.subheader("📊 Vendas por lanche")
        st.bar_chart(df["Lanche"].value_counts())