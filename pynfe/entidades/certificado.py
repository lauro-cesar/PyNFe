# -*- coding: utf-8 -*-

import os
import tempfile

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12

from .base import Entidade


class Certificado(Entidade):
    """Classe abstrata responsavel por definir o modelo padrao para as demais
    classes de certificados digitais.

    Caso va implementar um novo formato de certificado, crie uma classe que
    herde desta."""

    def __new__(cls, *args, **kwargs):
        if cls == Certificado:
            raise Exception("Esta classe nao pode ser instanciada diretamente!")
        else:
            return super(Certificado, cls).__new__(cls)


class CertificadoA1(Certificado):
    """Implementa a entidade do certificado eCNPJ A1, suportado pelo OpenSSL,
    e amplamente utilizado."""

    caminho_arquivo = None

    def __init__(self, caminho_arquivo=None):
        self.caminho_arquivo = caminho_arquivo
        self.arquivos_temp = []

    def separar_arquivo(self, senha, caminho=False):
        """Separa o arquivo de certificado em dois: de chave e de certificado e retorna a string.
        Se caminho for True grava na pasta temporaria e retorna o caminho dos arquivos,
        senao retorna o objeto. Apos o uso devem ser excluidos com o metodo excluir.
        """

        try:
            with open(self.caminho_arquivo, "rb") as cert_arquivo:
                cert_conteudo = cert_arquivo.read()
        except (PermissionError, FileNotFoundError) as exc:
            raise Exception(
                """Falha ao abrir arquivo do certificado digital A1.
                Verifique local e permissoes do arquivo."""
            ) from exc
        except Exception as exc:
            raise Exception(
                "Falha ao abrir arquivo do certificado digital A1. Causa desconhecida."
            ) from exc

        # Carrega o arquivo .pfx, erro pode ocorrer se a senha estiver errada ou formato invalido.
        try:
            (
                chave,
                cert,
                _,
            ) = pkcs12.load_key_and_certificates(cert_conteudo, str.encode(senha))
        except ValueError as e:
            if "bad decrypt" in str(e).lower():
                raise Exception(
                    "Falha ao carregar certificado digital A1. Verifique a senha do"
                    " certificado."
                ) from e
            else:
                raise Exception(
                    "Falha ao carregar certificado digital A1. Causa desconhecida."
                ) from e

        if caminho:
            # cria arquivos temporarios
            with tempfile.NamedTemporaryFile(delete=False) as arqcert:
                arqcert.write(cert.public_bytes(Encoding.PEM))
            with tempfile.NamedTemporaryFile(delete=False) as arqchave:
                arqchave.write(chave.private_bytes(Encoding.PEM))
            self.arquivos_temp.append(arqchave.name)
            self.arquivos_temp.append(arqcert.name)
            return arqchave.name, arqcert.name
        else:
            # Certificado
            cert = cert.public_bytes(Encoding.PEM).decode("utf-8")
            cert = cert.replace("\n", "")
            cert = cert.replace("-----BEGIN CERTIFICATE-----", "")
            cert = cert.replace("-----END CERTIFICATE-----", "")

            # Chave, string decodificada da chave privada
            chave = chave.private_bytes(Encoding.PEM)

            return chave, cert

    def excluir(self):
        """Exclui os arquivos temporarios utilizados para o request."""
        try:
            for i in self.arquivos_temp:
                os.remove(i)
            self.arquivos_temp.clear()
        except Exception:
            pass
