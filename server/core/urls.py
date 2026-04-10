from django.urls import path
from .views import WalletInfoView, RecommendedFeeView, TransactionListView, RBFView

urlpatterns = [
    path('wallet/info/', WalletInfoView.as_view()),
    path('fees/recommended/', RecommendedFeeView.as_view()),
    path('transactions/', TransactionListView.as_view()),
    path('transactions/<int:pk>/rbf/', RBFView.as_view())
]