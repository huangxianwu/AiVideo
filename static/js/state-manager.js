/**
 * 状态管理器 - 负责撤销功能和状态追踪
 */
class StateManager {
    constructor(maxHistorySize = 20) {
        this.undoStack = [];
        this.redoStack = [];
        this.maxHistorySize = maxHistorySize;
        this.currentState = null;
        this.hasUnsavedChanges = false;
    }
    
    /**
     * 保存当前状态
     */
    saveState(stateData, description = '') {
        try {
            // 如果有新的操作，清空重做栈
            this.redoStack = [];
            
            // 添加到撤销栈
            this.undoStack.push({
                data: stateData,
                description: description,
                timestamp: Date.now()
            });
            
            // 限制历史记录大小
            if (this.undoStack.length > this.maxHistorySize) {
                this.undoStack.shift();
            }
            
            this.currentState = stateData;
            this.hasUnsavedChanges = true;
            
            this.updateUndoRedoButtons();
            
            console.log(`状态已保存: ${description}`);
        } catch (error) {
            console.error('保存状态失败:', error);
        }
    }
    
    /**
     * 撤销操作
     */
    undo() {
        if (this.canUndo()) {
            try {
                // 将当前状态移到重做栈
                if (this.currentState) {
                    this.redoStack.push({
                        data: this.currentState,
                        description: '当前状态',
                        timestamp: Date.now()
                    });
                }
                
                // 从撤销栈获取上一个状态
                const previousState = this.undoStack.pop();
                this.currentState = previousState.data;
                
                this.updateUndoRedoButtons();
                
                console.log(`撤销操作: ${previousState.description}`);
                return previousState.data;
            } catch (error) {
                console.error('撤销操作失败:', error);
                return null;
            }
        }
        return null;
    }
    
    /**
     * 重做操作
     */
    redo() {
        if (this.canRedo()) {
            try {
                // 将当前状态移到撤销栈
                if (this.currentState) {
                    this.undoStack.push({
                        data: this.currentState,
                        description: '撤销前状态',
                        timestamp: Date.now()
                    });
                }
                
                // 从重做栈获取下一个状态
                const nextState = this.redoStack.pop();
                this.currentState = nextState.data;
                
                this.updateUndoRedoButtons();
                
                console.log(`重做操作: ${nextState.description}`);
                return nextState.data;
            } catch (error) {
                console.error('重做操作失败:', error);
                return null;
            }
        }
        return null;
    }
    
    /**
     * 检查是否可以撤销
     */
    canUndo() {
        return this.undoStack.length > 0;
    }
    
    /**
     * 检查是否可以重做
     */
    canRedo() {
        return this.redoStack.length > 0;
    }
    
    /**
     * 更新撤销/重做按钮状态
     */
    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('undoAction');
        const redoBtn = document.getElementById('redoAction');
        
        if (undoBtn) {
            undoBtn.disabled = !this.canUndo();
            undoBtn.title = this.canUndo() ? 
                `撤销: ${this.undoStack[this.undoStack.length - 1].description}` : 
                '无法撤销';
        }
        
        if (redoBtn) {
            redoBtn.disabled = !this.canRedo();
            redoBtn.title = this.canRedo() ? 
                `重做: ${this.redoStack[this.redoStack.length - 1].description}` : 
                '无法重做';
        }
    }
    
    /**
     * 清空历史记录
     */
    clearHistory() {
        this.undoStack = [];
        this.redoStack = [];
        this.currentState = null;
        this.updateUndoRedoButtons();
        console.log('历史记录已清空');
    }
    
    /**
     * 获取历史记录信息
     */
    getHistoryInfo() {
        return {
            undoCount: this.undoStack.length,
            redoCount: this.redoStack.length,
            maxSize: this.maxHistorySize,
            hasUnsavedChanges: this.hasUnsavedChanges
        };
    }
    
    /**
     * 标记为已保存
     */
    markAsSaved() {
        this.hasUnsavedChanges = false;
        console.log('状态已标记为已保存');
    }
    
    /**
     * 检查是否有未保存的更改
     */
    hasUnsaved() {
        return this.hasUnsavedChanges;
    }
    
    /**
     * 获取当前状态
     */
    getCurrentState() {
        return this.currentState;
    }
    
    /**
     * 设置初始状态
     */
    setInitialState(stateData) {
        this.currentState = stateData;
        this.hasUnsavedChanges = false;
        this.clearHistory();
        console.log('初始状态已设置');
    }
    
    /**
     * 获取历史记录列表（用于调试）
     */
    getHistoryList() {
        return {
            undo: this.undoStack.map(state => ({
                description: state.description,
                timestamp: new Date(state.timestamp).toLocaleString()
            })),
            redo: this.redoStack.map(state => ({
                description: state.description,
                timestamp: new Date(state.timestamp).toLocaleString()
            }))
        };
    }
    
    /**
     * 压缩历史记录（移除过旧的记录）
     */
    compressHistory() {
        const compressionThreshold = Math.floor(this.maxHistorySize * 0.7);
        
        if (this.undoStack.length > compressionThreshold) {
            const removeCount = this.undoStack.length - compressionThreshold;
            this.undoStack.splice(0, removeCount);
            console.log(`历史记录已压缩，移除了 ${removeCount} 条记录`);
        }
    }
    
    /**
     * 销毁状态管理器
     */
    destroy() {
        this.clearHistory();
        this.currentState = null;
        this.hasUnsavedChanges = false;
    }
}