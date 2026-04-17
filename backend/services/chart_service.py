import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from io import BytesIO

class ChartService:
    def __init__(self):
        # Configurar backend de Matplotlib para evitar errores en servidores sin interfaz gráfica
        import matplotlib
        matplotlib.use('Agg')

    def generate_year_chart(self, pubs_by_year):
        """Genera un gráfico de línea para la producción por año."""
        if not pubs_by_year: return None
        
        years = sorted([int(k) for k in pubs_by_year.keys()])
        counts = [pubs_by_year[str(y)] for y in years]
        
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(years, counts, marker="o", color="#2E75B6", linewidth=2.5, markersize=7)
        
        for x, y in zip(years, counts):
            ax.annotate(f"{y:,}", (x, y), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9)
        
        ax.set_xlabel("Año", fontsize=10)
        ax.set_ylabel("Documentos", fontsize=10)
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) for y in years], rotation=0, fontsize=9)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf

    def generate_country_chart(self, pubs_by_country, top_n=15):
        """Genera un gráfico de barras horizontales para la distribución por país."""
        if not pubs_by_country: return None
        
        # pubs_by_country es una lista de dicts: [{"country": ..., "count": ...}, ...]
        data = sorted(pubs_by_country, key=lambda x: x["count"], reverse=True)[:top_n]
        data = sorted(data, key=lambda x: x["count"]) # Menor a mayor para barras horizontales
        
        countries = [d["country"] for d in data]
        counts = [d["count"] for d in data]
        
        # Degradado de azul
        n = len(countries)
        colors = [plt.cm.Blues(0.4 + 0.55 * (i / max(n - 1, 1))) for i in range(n)]
        
        fig, ax = plt.subplots(figsize=(9, max(3.5, n * 0.38)))
        bars = ax.barh(countries, counts, color=colors, edgecolor="white", height=0.65)
        
        max_val = max(counts) if counts else 0
        for bar, val in zip(bars, counts):
            ax.text(bar.get_width() + max_val * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:,}", va="center", ha="left", fontsize=9)
        
        ax.set_xlabel("Documentos", fontsize=10)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.set_xlim(0, max_val * 1.15 if max_val > 0 else 1)
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf
