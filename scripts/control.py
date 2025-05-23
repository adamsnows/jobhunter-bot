#!/usr/bin/env python3
"""
JobHunter Bot Control Script
Script para controlar o daemon do JobHunter Bot
"""

import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path

# Add backend src to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir / "src"))

def get_pid():
    """Obtém PID do daemon se estiver rodando"""
    pid_file = "/tmp/jobhunter_daemon.pid"

    if not os.path.exists(pid_file):
        return None

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Verifica se processo existe
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        # Remove arquivo PID inválido
        try:
            os.remove(pid_file)
        except OSError:
            pass
        return None

def is_running():
    """Verifica se o daemon está rodando"""
    return get_pid() is not None

def start_daemon(config_file=None, test_mode=False):
    """Inicia o daemon"""
    if is_running():
        print("❌ Daemon já está rodando!")
        return False

    print("🚀 Iniciando JobHunter Bot Daemon...")

    # Prepara comando
    cmd = [sys.executable, str(backend_dir / "src" / "bot" / "job_hunter_daemon.py")]

    if config_file:
        cmd.extend(["--config", config_file])

    if test_mode:
        cmd.append("--test")

    try:
        # Inicia processo em background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Aguarda um pouco para verificar se iniciou
        time.sleep(2)

        if is_running():
            print("✅ Daemon iniciado com sucesso!")
            print(f"📊 PID: {get_pid()}")
            return True
        else:
            print("❌ Falha ao iniciar daemon")
            return False

    except Exception as e:
        print(f"❌ Erro ao iniciar daemon: {str(e)}")
        return False

def stop_daemon():
    """Para o daemon"""
    pid = get_pid()

    if not pid:
        print("❌ Daemon não está rodando")
        return False

    print(f"🛑 Parando daemon (PID: {pid})...")

    try:
        # Envia SIGTERM
        os.kill(pid, signal.SIGTERM)

        # Aguarda até 10 segundos para parar graciosamente
        for _ in range(10):
            time.sleep(1)
            if not is_running():
                print("✅ Daemon parado com sucesso!")
                return True

        # Se não parou, força com SIGKILL
        print("⚠️ Forçando parada...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)

        if not is_running():
            print("✅ Daemon parado com sucesso!")
            return True
        else:
            print("❌ Não foi possível parar o daemon")
            return False

    except OSError as e:
        print(f"❌ Erro ao parar daemon: {str(e)}")
        return False

def restart_daemon(config_file=None, test_mode=False):
    """Reinicia o daemon"""
    print("🔄 Reiniciando daemon...")

    if is_running():
        stop_daemon()
        time.sleep(2)

    return start_daemon(config_file, test_mode)

def status_daemon():
    """Mostra status do daemon"""
    pid = get_pid()

    if pid:
        print(f"✅ Daemon está rodando (PID: {pid})")

        # Mostra informações adicionais se possível
        try:
            import psutil
            process = psutil.Process(pid)

            print(f"📊 Status: {process.status()}")
            print(f"⏱️  Uptime: {time.time() - process.create_time():.0f}s")
            print(f"💾 Memória: {process.memory_info().rss / 1024 / 1024:.1f}MB")

        except ImportError:
            print("ℹ️  Instale 'psutil' para mais detalhes")
        except Exception as e:
            print(f"⚠️  Erro ao obter detalhes: {str(e)}")
    else:
        print("❌ Daemon não está rodando")

def logs_daemon(lines=50, follow=False):
    """Mostra logs do daemon"""
    log_file = backend_dir / "data" / "logs" / "jobhunter.log"

    if not log_file.exists():
        print("❌ Arquivo de log não encontrado")
        return

    if follow:
        print(f"📋 Seguindo logs (Ctrl+C para parar)...")
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            print("\n👋 Parando visualização de logs")
    else:
        print(f"📋 Últimas {lines} linhas do log:")
        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), str(log_file)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except Exception as e:
            print(f"❌ Erro ao ler logs: {str(e)}")

def install_service():
    """Instala como serviço do sistema (systemd)"""
    if os.geteuid() != 0:
        print("❌ Execute como root para instalar serviço")
        return False

    service_content = f"""[Unit]
Description=JobHunter Bot Daemon
After=network.target

[Service]
Type=forking
User=nobody
WorkingDirectory={backend_dir.parent}
ExecStart={sys.executable} {backend_dir / "src" / "bot" / "job_hunter_daemon.py"}
PIDFile=/tmp/jobhunter_daemon.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = "/etc/systemd/system/jobhunter-bot.service"

    try:
        with open(service_file, 'w') as f:
            f.write(service_content)

        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", "jobhunter-bot"])

        print("✅ Serviço instalado com sucesso!")
        print("🔧 Use: sudo systemctl start jobhunter-bot")
        return True

    except Exception as e:
        print(f"❌ Erro ao instalar serviço: {str(e)}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="JobHunter Bot Control Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  ./control.py start                    # Inicia daemon
  ./control.py start --test             # Inicia em modo teste
  ./control.py stop                     # Para daemon
  ./control.py restart                  # Reinicia daemon
  ./control.py status                   # Mostra status
  ./control.py logs                     # Mostra logs
  ./control.py logs --follow            # Segue logs em tempo real
        """
    )

    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status', 'logs', 'install'],
        help='Ação a executar'
    )

    parser.add_argument(
        '--config',
        default='.env',
        help='Arquivo de configuração (padrão: .env)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo de teste'
    )

    parser.add_argument(
        '--lines',
        type=int,
        default=50,
        help='Número de linhas do log (padrão: 50)'
    )

    parser.add_argument(
        '--follow',
        action='store_true',
        help='Seguir logs em tempo real'
    )

    args = parser.parse_args()

    # Verifica se está no diretório correto
    if not backend_dir.exists():
        print("❌ Execute o script do diretório raiz do projeto")
        sys.exit(1)

    # Executa ação
    try:
        if args.action == 'start':
            success = start_daemon(args.config, args.test)
        elif args.action == 'stop':
            success = stop_daemon()
        elif args.action == 'restart':
            success = restart_daemon(args.config, args.test)
        elif args.action == 'status':
            status_daemon()
            success = True
        elif args.action == 'logs':
            logs_daemon(args.lines, args.follow)
            success = True
        elif args.action == 'install':
            success = install_service()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n👋 Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
