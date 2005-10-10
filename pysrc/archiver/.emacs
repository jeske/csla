
(setq load-path (cons "~/.emacslib/" load-path))

;
; bbdb
;(setq load-path (cons "~/bbdb/bbdb-2.00/lisp" load-path))
;(require 'bbdb)
;(bbdb-initialize)


; the backup files should be . files so they are hidden!
(defun make-backup-file-name (filename)
  (expand-file-name
    (concat "." (file-name-nondirectory filename) "~")
    (file-name-directory filename)))

; (load-file '"~/.emacslib/python-mode.el")
; (autoload 'vm "vm" "Start VM" t)

(load-file '"~/.emacslib/filladapt.el")
(require 'filladapt)
(setq-default filladapt-mode t)
(setq filladapt-mode-line-string " FA"
      filladapt-token-table (append '(("\\([Pp]\\. ?\\)+[Ss]\\." ps-ending)
                                      ("|" citation->))
                                    filladapt-token-table)
      filladapt-token-conversion-table (cons '(ps-ending . spaces)
                                             filladapt-token-conversion-table
)
      )

(setq auto-mode-alist (cons '("\\.py$" . python-mode) auto-mode-alist))
(setq interpreter-mode-alist
      (cons '("python" . python-mode)
            interpreter-mode-alist))
(autoload 'python-mode "python-mode" "" t)
(setq indent-tabs-mode nil)

(setq py-indent-offset 4)

; no more perforce... :(
; (load-library "p4")

(custom-set-variables
 '(user-mail-address "jeske@home.chat.net" t)
 '(query-user-mail-address nil)
 '(bbdb-offer-save "no")
)

(require 'filladapt)
(setq-default filladapt-mode t)            
(add-hook 'text-mode-hook 'turn-on-filladapt-mode)

(global-set-key "\C-cg"       'goto-line)
(global-set-key "\M-g"       'goto-line)
(custom-set-faces)

(global-set-key "\C-j" 'dabbrev-expand)
 

(setq c-mode-hook
      '(lambda ()
         (auto-fill-mode 0)))


(setq c++-mode-hook
      '(lambda ()
                                 (local-set-key "\C-j" 'dabbrev-expand)
         (auto-fill-mode 0)))

(setq python-mode-hook
      '(lambda ()
      (local-set-key "\C-j" 'dabbrev-expand)
      (setq py-smart-indentation nil)
      (setq indent-tabs-mode nil)
      (set-face-background 'modeline "red" (current-buffer))
;      (setq modeline-format
;           (list ""
;                 'modeline-modified
;                 '(line-number-mode "(L%l,") 
;                 '(column-number-mode "C%c)-")
;                 "%b--"
;                 ":"
;                 'default-directory

;                 "   "
;                 'global-mode-string
;                 "   %[("  
;                 'mode-name
;                 'modeline-process 
;                 'minor-mode-alist
;                 "%n"
;                 ")%]----"

;                 '(-3 . "%p")
;                 "-%-"))


      ))

