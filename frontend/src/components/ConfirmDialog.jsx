import './ConfirmDialog.css'

function ConfirmDialog({ message, onConfirm, onCancel, title = 'Confirm' }) {
  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <h3 className="confirm-title">{title}</h3>
        <p className="confirm-message">{message}</p>
        <div className="confirm-actions">
          <button className="btn-confirm-cancel" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-confirm-ok" onClick={onConfirm}>
            Confirm
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog

