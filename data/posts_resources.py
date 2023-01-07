from flask import jsonify
from flask_restful import abort, Resource

from data import db_session
from data.posts import Posts
from data.reqparse import parser


def abort_if_posts_not_found(posts_id):
    session = db_session.create_session()
    posts = session.query(Posts).get(posts_id)
    if not posts:
        abort(404, message=f"Posts {posts_id} not found")

class PostsResource(Resource):
    def get(self, posts_id):
        abort_if_posts_not_found(posts_id)
        session = db_session.create_session()
        posts = session.query(Posts).get(posts_id)
        return jsonify({'posts': posts.to_dict(
            only=('title', 'content', 'user_id', 'is_private'))})

    def delete(self, posts_id):
        abort_if_posts_not_found(posts_id)
        session = db_session.create_session()
        posts = session.query(Posts).get(posts_id)
        session.delete(posts)
        session.commit()
        return jsonify({'success': 'OK'})


class PostsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        posts = session.query(Posts).all()
        return jsonify({'posts': [item.to_dict(
            only=('title', 'content')) for item in posts]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        posts = Posts(
            title=args['title'],
            content=args['content'],
            user_id=args['user_id'],
            is_published=args['is_published'],
            is_private=args['is_private']
        )
        session.add(posts)
        session.commit()
        return jsonify({'success': 'OK'})