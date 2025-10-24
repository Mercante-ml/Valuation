# reports/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ValuationReport

@login_required # Garante que apenas usuários logados acessem
def report_history_view(request):
    """
    View para a página 'Meu Histórico'.
    Busca todos os relatórios pertencentes ao usuário logado.
    """
    
    # 1. Busca no banco de dados
    # Filtra os relatórios para mostrar APENAS os do usuário atual (request.user)
    # Ordena pelos mais recentes primeiro
    user_reports = ValuationReport.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. Define o contexto para enviar ao template
    context = {
        'reports': user_reports
    }
    
    # 3. Renderiza o novo template que vamos criar
    return render(request, 'reports/report_history.html', context)


@login_required
def report_detail_view(request, pk):
    """
    View para a página de 'Detalhe do Relatório'.
    Mostra os resultados de um relatório específico.
    'pk' (Primary Key) é o ID do relatório vindo da URL.
    """
    
    # 1. Busca o relatório específico.
    # get_object_or_404 é um atalho do Django que:
    # - Tenta buscar o relatório (pk=pk, user=request.user)
    # - Se não encontrar (ou se o relatório for de OUTRO usuário), 
    #   ele automaticamente retorna um erro 404 (Not Found).
    # Isso é EXCELENTE para segurança.
    report = get_object_or_404(ValuationReport, pk=pk, user=request.user)
    
    # 2. Define o contexto
    context = {
        'report': report
        # O 'result_data' (JSON com o feedback da IA)
        # estará dentro de 'report.result_data'
    }
    
    # 3. Renderiza o template de detalhe
    return render(request, 'reports/report_detail.html', context)