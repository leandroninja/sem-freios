# Corrida Maluca

Jogo de corrida em Python onde voce controla um carro e precisa desviar do trafego pelo maior tempo possivel.

## Como jogar

```bash
python -m pip install pygame
python jogo.py
```

## Controles

| Tecla | Acao |
|-------|------|
| Setas | Mover o carro |
| ESC | Pausar / Continuar |
| ENTER / ESPACO | Iniciar / Reiniciar |
| Q | Voltar ao menu |

## Funcionalidades

- Menu principal com fundo animado e recorde salvo
- Sistema de 3 vidas com periodo de invencibilidade apos colisao
- Pontuacao baseada em tempo de sobrevivencia (segundos)
- Dificuldade progressiva: velocidade aumenta a cada 10 segundos
- Recorde salvo em arquivo local (`highscore.json`)
- Efeito de screen shake ao colidir
- Explosao de particulas na colisao
- Linhas de velocidade que aparecem conforme o jogo acelera
- HUD com tempo, recorde, nivel de velocidade e coracoes de vida
- Tela de pausa e tela de game over
- Fundo com scroll continuo
- Carro pisca durante invencibilidade

## Requisitos

- Python 3.10+
- Pygame

## Estrutura

```
jogo/
├── jogo.py          # Codigo principal
├── highscore.json   # Recorde (gerado automaticamente)
├── pista.png        # Fundo da pista
├── carro1.png       # Carro do jogador
├── carro2-9.png     # Carros inimigos
├── jipe.png         # Jipe inimigo
└── jipe1.png        # Jipe inimigo variante
```
