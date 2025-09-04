// ERP系统脚本

document.addEventListener('DOMContentLoaded', function() {
    // 侧边栏折叠/展开功能
    const sidebar = document.querySelector('.erp-sidebar');
    const toggleBtn = document.querySelector('#sidebarToggle');
    const mainContent = document.querySelector('.erp-main-content');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('expanded');
            // 保存侧边栏状态到本地存储
            localStorage.setItem('sidebarExpanded', sidebar.classList.contains('expanded'));
        });
        
        // 从本地存储加载侧边栏状态
        const sidebarExpanded = localStorage.getItem('sidebarExpanded') === 'true';
        if (sidebarExpanded) {
            sidebar.classList.add('expanded');
        } else {
            sidebar.classList.remove('expanded');
        }
    }
    
    // 激活当前页面的菜单项
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
    
    // 全局选择状态管理
    window.selectedProducts = new Set();
    
    // 产品卡片选择功能
    window.toggleCardSelection = function(productId) {
        const card = document.querySelector(`[data-product-id="${productId}"]`);
        if (!card) {
            console.error('Product card not found:', productId);
            return;
        }
        
        const checkbox = card.querySelector('.absolute.top-2.left-2');
        if (!checkbox) {
            console.error('Checkbox not found for product:', productId);
            return;
        }
        
        const checkIcon = checkbox.querySelector('i');
        if (!checkIcon) {
            console.error('Check icon not found for product:', productId);
            return;
        }
        
        if (window.selectedProducts.has(productId)) {
            // 取消选择
            window.selectedProducts.delete(productId);
            card.classList.remove('selected');
            checkIcon.classList.add('hidden');
        } else {
            // 选择
            window.selectedProducts.add(productId);
            card.classList.add('selected');
            checkIcon.classList.remove('hidden');
        }
        
        updateSelectedCount();
    };
    
    // 更新卡片选择状态的函数
    function updateCardSelection(card, isSelected) {
        if (isSelected) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    }
    
    // 更新已选择数量的函数
    function updateSelectedCount() {
        const selectedCountElement = document.getElementById('selectedCount');
        if (selectedCountElement) {
            selectedCountElement.textContent = window.selectedProducts.size;
        }
    }
    
    // 初始化更新选择数量
    updateSelectedCount();
    
    // 图片放大功能
    window.openImageModal = function(imageSrc, productName) {
        const imageModal = document.getElementById('imageModal');
        const modalImg = document.getElementById('modalImage');
        
        if (imageModal && modalImg) {
            modalImg.src = imageSrc;
            modalImg.alt = productName;
            imageModal.classList.remove('hidden');
            imageModal.classList.add('show');
        }
    };
    
    window.closeImageModal = function() {
        const imageModal = document.getElementById('imageModal');
        if (imageModal) {
            imageModal.classList.add('hidden');
            imageModal.classList.remove('show');
        }
    };
    
    // 跳转到已选商品页面
    window.goToSelectedPage = function() {
        if (window.selectedProducts.size === 0) {
            showToast('请先选择商品', 'warning');
            return;
        }
        
        // 将选中的商品ID转换为数组并传递给已选商品页面
        const selectedIds = Array.from(window.selectedProducts);
        const params = new URLSearchParams();
        params.append('selected_ids', selectedIds.join(','));
        
        window.location.href = '/erp/selected?' + params.toString();
    };
    
    // CSV导入功能
    const importCsvBtn = document.getElementById('import-csv');
    const csvFileInput = document.getElementById('csv-file-input');
    
    if (importCsvBtn && csvFileInput) {
        importCsvBtn.addEventListener('click', function() {
            csvFileInput.click();
        });
        
        csvFileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const formData = new FormData();
                formData.append('csv_file', this.files[0]);
                
                // 显示加载动画
                showLoading();
                
                fetch('/import-csv', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // 隐藏加载动画
                    hideLoading();
                    
                    // 显示结果通知
                    showToast(data.message, data.success ? 'success' : 'error');
                    
                    // 如果成功，刷新页面显示新数据
                    if (data.success) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    }
                })
                .catch(error => {
                    console.error('Error importing CSV:', error);
                    // 隐藏加载动画
                    hideLoading();
                    showToast('导入CSV时发生错误', 'error');
                });
                
                // 重置文件输入，以便可以再次选择同一文件
                this.value = '';
            }
        });
    }
    
    // 刷新数据功能
    function refreshData() {
        showLoading();
        
        fetch('/api/refresh')
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.success) {
                    showToast(data.message, 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('刷新失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error refreshing data:', error);
                hideLoading();
                showToast('网络错误', 'error');
            });
    }
    
    // 将refreshData函数暴露到全局作用域
    window.refreshData = refreshData;
    
    // 加载动画控制
    function showLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
            loadingElement.classList.add('show');
        }
    }
    
    function hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.classList.add('hidden');
            loadingElement.classList.remove('show');
        }
    }
    
    // Toast通知控制
    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        const toastIcon = document.getElementById('toastIcon');
        
        if (toast && toastMessage && toastIcon) {
            // 设置消息内容
            toastMessage.textContent = message;
            
            // 设置图标和颜色
            const iconClasses = {
                'success': 'fas fa-check-circle text-green-500',
                'error': 'fas fa-exclamation-circle text-red-500',
                'warning': 'fas fa-exclamation-triangle text-yellow-500',
                'info': 'fas fa-info-circle text-blue-500'
            };
            
            toastIcon.className = iconClasses[type] || iconClasses['info'];
            
            // 显示Toast
            toast.classList.remove('hidden', 'translate-x-full');
            toast.classList.add('show');
            
            // 3秒后隐藏
            setTimeout(() => {
                hideToast();
            }, 3000);
        }
    }
    
    window.hideToast = function() {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.classList.remove('show');
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 300);
        }
    };
    
    // 暴露函数到全局作用域
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;
    window.showToast = showToast;
});