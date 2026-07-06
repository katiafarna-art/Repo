from core.data.entities.embedder.ada_embedder import AdaEmbedder
from core.data.entities.embedder.isp_embedder import ISPEmbedder

dct_embedder_factory = {"ada-embedder": AdaEmbedder, "isp-embedder": ISPEmbedder}
