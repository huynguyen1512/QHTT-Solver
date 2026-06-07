import streamlit as st
import pandas as pd
import re
from fractions import Fraction

# ==========================================
# CÁC HÀM HỖ TRỢ LATEX VÀ TOÁN HỌC
# ==========================================
def to_latex_frac(val: Fraction):
    """Chuyển đổi Fraction thành chuỗi phân số LaTeX"""
    if val.denominator == 1:
        return str(val.numerator)
    if val.numerator < 0:
        return f"-\\frac{{{-val.numerator}}}{{{val.denominator}}}"
    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def format_term(coef: Fraction, var_name: str, is_first: bool = False):
    """Định dạng một số hạng trong phương trình đại số"""
    if coef == 0:
        return ""
    
    sign_str = ""
    if is_first:
        if coef < 0: sign_str = "-"
    else:
        sign_str = " + " if coef > 0 else " - "
        
    abs_coef = abs(coef)
    coef_str = "" if abs_coef == 1 else to_latex_frac(abs_coef)
    
    return f"{sign_str}{coef_str}{var_name}"

# ==========================================
# LÕI THUẬT TOÁN ĐƠN HÌNH TỪ VỰNG
# ==========================================
class SimplexDictionary:
    def __init__(self, c_dict, A_dict, b_dict, original_v, method_choice):
        self.N = list(c_dict.keys())
        self.B = list(b_dict.keys())
        self.c = c_dict.copy()
        self.A = {i: A_dict[i].copy() for i in self.B}
        self.b = b_dict.copy()
        self.v = original_v
        
        self.method = method_choice
        self.steps_log = []
        
    def var_sort_key(self, var_str):
        """Hàm sắp xếp biến: x ưu tiên trước w, sau đó sắp xếp theo số tự nhiên"""
        nums = re.findall(r'\d+', var_str)
        num = int(nums[0]) if nums else 0
        prefix_score = 0 if 'x' in var_str else 1
        return (prefix_score, num, var_str)
        
    def log_dictionary(self, title, entering=None, leaving=None, is_phase1=False):
        """Xuất từ vựng: Hàm mục tiêu ở trên, kẻ ngang, rồi tới ràng buộc ở dưới."""
        latex_str = f"**{title}**\n\n"
        latex_str += "$$\n\\begin{array}{r c l}\n"
        
        # Phần 1: Phương trình hàm mục tiêu (Z hoặc W phụ) nằm TRÊN CÙNG
        obj_rhs = ""
        first_term = True
        if self.v != 0 or all(self.c[j] == 0 for j in self.N):
            obj_rhs += to_latex_frac(self.v)
            first_term = False
            
        for j in self.N:
            coef = self.c[j]
            if coef != 0:
                var_j_str = f"\\overset{{\\downarrow}}{{{j}}}" if j == entering else j
                obj_rhs += format_term(coef, var_j_str, is_first=first_term)
                first_term = False
                
        if obj_rhs == "": obj_rhs = "0"
        
        obj_name = "w_{aux}" if is_phase1 else "Z"
        latex_str += f"{obj_name} & = & {obj_rhs} \\\\\n"
        latex_str += "\\hline\n"
        
        # Phần 2: Phương trình của các biến cơ sở (w_i hoặc x_i) nằm BÊN DƯỚI
        for i in self.B:
            var_i_str = f"\\leftarrow {i}" if i == leaving else i
            rhs = ""
            first_term = True
            
            if self.b[i] != 0 or all(self.A[i][j] == 0 for j in self.N):
                rhs += to_latex_frac(self.b[i])
                first_term = False
                
            for j in self.N:
                coef = -self.A[i][j]
                if coef != 0:
                    var_j_str = f"\\overset{{\\downarrow}}{{{j}}}" if j == entering else j
                    rhs += format_term(coef, var_j_str, is_first=first_term)
                    first_term = False
                    
            if rhs == "": rhs = "0"
            latex_str += f"{var_i_str} & = & {rhs} \\\\\n"
            
        latex_str += "\\end{array}\n$$\n"
        self.steps_log.append(latex_str)

    def pivot(self, entering, leaving):
        """Thực hiện một phép xoay (Pivot)"""
        A_rk = self.A[leaving][entering]
        new_b_leaving = self.b[leaving] / A_rk
        new_A_leaving = {}
        
        for j in self.N:
            if j == entering:
                new_A_leaving[leaving] = Fraction(1) / A_rk
            else:
                new_A_leaving[j] = self.A[leaving][j] / A_rk

        for i in self.B:
            if i == leaving: continue
            A_ik = self.A[i][entering]
            self.b[i] -= A_ik * new_b_leaving
            for j in self.N:
                if j == entering:
                    self.A[i][leaving] = -A_ik * new_A_leaving[leaving]
                else:
                    self.A[i][j] -= A_ik * new_A_leaving[j]
            del self.A[i][entering]

        c_k = self.c[entering]
        self.v += c_k * new_b_leaving
        for j in self
