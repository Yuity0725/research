from concurrent.futures import BrokenExecutor
from flask import Blueprint, render_template

bp = Blueprint('bp_img', __name__, static_folder='../FashionIQ_dataset/images')

@bp.route('/bp_index')
def search():
    return render_template('bp_index.html')